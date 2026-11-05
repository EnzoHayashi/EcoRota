""" Para rodar: python server.py e abrir http://localhost:8000 """

import json
import math
import os
import random
import sqlite3
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_BD = os.path.join(PASTA, "coleta.db")

GARAGEM = (-23.5600, -46.5600)   
FATOR_URBANO = 1.3               
VELOCIDADE_KMH = 25              
MIN_POR_PONTO = 3                
KG_POR_LITRO = 0.2               
FORMATO_DATA = "%Y-%m-%d %H:%M:%S"



def conectar():
    con = sqlite3.connect(ARQUIVO_BD)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def criar_banco():
    """Na primeira execução cria as tabelas, os dados de exemplo e o histórico."""
    if os.path.exists(ARQUIVO_BD):
        return
    con = conectar()
    for arquivo in ("schema.sql", "seed.sql"):
        with open(os.path.join(PASTA, arquivo), encoding="utf-8") as f:
            con.executescript(f.read())
    gerar_leituras_e_historico(con)
    con.commit()
    con.close()


def gerar_leituras_e_historico(con):
    random.seed(42)
    agora = datetime.now()

    for sensor in con.execute("SELECT id_sensor FROM sensor_nivel").fetchall():
        nivel_final = random.uniform(15, 98)
        for i in range(6):
            quando = agora - timedelta(hours=(5 - i) * 4)
            con.execute(
                "INSERT INTO leitura_sensor (nivel_percentual, timestamp_leitura, id_sensor) VALUES (?, ?, ?)",
                (round(nivel_final * (i + 1) / 6, 2), quando.strftime(FORMATO_DATA), sensor["id_sensor"]),
            )

    pontos = pontos_da_rota_fixa(con)
    km_fixa = km_percurso(pontos)
    consumo = con.execute("SELECT consumo_medio_km_l FROM caminhao WHERE id_caminhao = 1").fetchone()[0]
    for dias_atras in range(5, 0, -1):
        inicio = (agora - timedelta(days=dias_atras)).replace(hour=6, minute=0, second=0)
        km = round(km_fixa * random.uniform(0.95, 1.05), 2)
        fim = inicio + timedelta(minutes=tempo_min(km, len(pontos)))
        con.execute(
            """INSERT INTO execucao_rota (data, hora_inicio, hora_fim, distancia_percorrida_km,
               combustivel_consumido_l, volume_coletado_kg, id_rota, id_caminhao, id_motorista)
               VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?)""",
            (inicio.strftime("%Y-%m-%d"), inicio.strftime("%H:%M"), fim.strftime("%H:%M"), km,
             round(km / consumo, 2), round(random.uniform(2500, 4000), 2), random.choice([1, 2])),
        )



def listar_conteineres(con):
    """Cada contêiner com a LEITURA MAIS RECENTE do seu sensor."""
    linhas = con.execute(
        """SELECT c.id_conteiner, c.capacidade_litros, t.descricao AS tipo,
                  p.id_ponto, p.endereco, p.latitude, p.longitude, b.nome AS bairro,
                  l.nivel_percentual AS nivel, l.timestamp_leitura AS lido_em
           FROM conteiner c
           JOIN ponto_coleta p  ON p.id_ponto = c.id_ponto
           JOIN bairro b        ON b.id_bairro = p.id_bairro
           JOIN tipo_residuo t  ON t.id_tipo = c.id_tipo
           JOIN sensor_nivel s  ON s.id_conteiner = c.id_conteiner
           JOIN leitura_sensor l ON l.id_sensor = s.id_sensor
           WHERE l.id_leitura = (SELECT MAX(l2.id_leitura) FROM leitura_sensor l2
                                 WHERE l2.id_sensor = s.id_sensor)
           ORDER BY c.id_conteiner"""
    ).fetchall()
    return [dict(l) for l in linhas]


def pontos_da_rota_fixa(con):
    linhas = con.execute(
        """SELECT p.* FROM rota_ponto rp JOIN ponto_coleta p ON p.id_ponto = rp.id_ponto
           WHERE rp.id_rota = 1 ORDER BY rp.ordem_visita"""
    ).fetchall()
    return [dict(l) for l in linhas]


def listar_historico(con):
    linhas = con.execute(
        """SELECT e.id_execucao, e.data, e.hora_inicio, e.hora_fim,
                  e.distancia_percorrida_km AS distancia_km, e.combustivel_consumido_l AS combustivel_l,
                  e.volume_coletado_kg AS volume_kg, e.id_rota,
                  (SELECT COUNT(*) FROM rota_ponto rp WHERE rp.id_rota = e.id_rota) AS pontos
           FROM execucao_rota e ORDER BY e.id_execucao DESC LIMIT 10"""
    ).fetchall()
    return [dict(l) for l in linhas]



def distancia_km(a, b):
    """Distância entre dois pontos (lat, lng) pela fórmula de Haversine."""
    raio_terra = 6371
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * raio_terra * math.asin(math.sqrt(h)) * FATOR_URBANO


def km_percurso(pontos):
    """Garagem -> pontos na ordem dada -> garagem."""
    total, atual = 0.0, GARAGEM
    for p in pontos:
        destino = (p["latitude"], p["longitude"])
        total += distancia_km(atual, destino)
        atual = destino
    return total + distancia_km(atual, GARAGEM)


def vizinho_mais_proximo(pontos):
    """Heurística simples: a cada passo vai ao ponto não visitado mais perto."""
    atual, restantes, ordem = GARAGEM, list(pontos), []
    while restantes:
        prox = min(restantes, key=lambda p: distancia_km(atual, (p["latitude"], p["longitude"])))
        ordem.append(prox)
        restantes.remove(prox)
        atual = (prox["latitude"], prox["longitude"])
    return ordem


def tempo_min(km, n_pontos):
    return round(km / VELOCIDADE_KMH * 60 + n_pontos * MIN_POR_PONTO)


def montar_plano(con, limite):
    consumo = con.execute("SELECT consumo_medio_km_l FROM caminhao WHERE id_caminhao = 1").fetchone()[0]

    
    fixa_pts = pontos_da_rota_fixa(con)
    km_fixa = km_percurso(fixa_pts)

    
    cheios = [c for c in listar_conteineres(con) if c["nivel"] >= limite]
    ordem = vizinho_mais_proximo(cheios)
    km_otim = km_percurso(ordem) if ordem else 0.0

    economia = round((1 - km_otim / km_fixa) * 100, 1) if km_fixa else 0
    return {
        "limite": limite,
        "garagem": {"latitude": GARAGEM[0], "longitude": GARAGEM[1]},
        "fixa": {
            "pontos": len(fixa_pts), "km": round(km_fixa, 2),
            "litros": round(km_fixa / consumo, 2), "tempo_min": tempo_min(km_fixa, len(fixa_pts)),
        },
        "otimizada": {
            "pontos": len(ordem), "km": round(km_otim, 2),
            "litros": round(km_otim / consumo, 2), "tempo_min": tempo_min(km_otim, len(ordem)) if ordem else 0,
            "ordem": [
                {"ordem": i + 1, "id_conteiner": c["id_conteiner"], "id_ponto": c["id_ponto"],
                 "endereco": c["endereco"], "bairro": c["bairro"], "nivel": c["nivel"],
                 "capacidade_litros": c["capacidade_litros"],
                 "latitude": c["latitude"], "longitude": c["longitude"]}
                for i, c in enumerate(ordem)
            ],
        },
        "economia_km_pct": economia,
        "economia_litros": round((km_fixa - km_otim) / consumo, 2),
    }



def simular_leituras(con):
    """Simula a passagem do tempo: cada sensor envia uma nova leitura mais alta."""
    agora = datetime.now().strftime(FORMATO_DATA)
    for c in listar_conteineres(con):
        sensor = con.execute("SELECT id_sensor FROM sensor_nivel WHERE id_conteiner = ?",
                             (c["id_conteiner"],)).fetchone()
        novo = min(100.0, round(c["nivel"] + random.uniform(5, 20), 2))
        con.execute("INSERT INTO leitura_sensor (nivel_percentual, timestamp_leitura, id_sensor) VALUES (?, ?, ?)",
                    (novo, agora, sensor["id_sensor"]))
    con.commit()


def registrar_execucao(con, limite):
    """Grava a rota otimizada como rota nova + execução no histórico e esvazia os contêineres."""
    plano = montar_plano(con, limite)
    otim = plano["otimizada"]
    if not otim["ordem"]:
        raise ValueError("Nenhum contêiner está acima do limite: não há o que coletar.")

    agora = datetime.now()
    dia = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][agora.weekday()]
    turno = "Manhã" if agora.hour < 12 else "Tarde" if agora.hour < 18 else "Noite"

    cur = con.execute("INSERT INTO rota (turno, dia_semana, distancia_planejada_km) VALUES (?, ?, ?)",
                      (turno, dia, otim["km"]))
    id_rota = cur.lastrowid
    for item in otim["ordem"]:
        con.execute("INSERT INTO rota_ponto (id_rota, id_ponto, ordem_visita) VALUES (?, ?, ?)",
                    (id_rota, item["id_ponto"], item["ordem"]))

    volume = sum(i["capacidade_litros"] * i["nivel"] / 100 * KG_POR_LITRO for i in otim["ordem"])
    fim = agora + timedelta(minutes=otim["tempo_min"])
    con.execute(
        """INSERT INTO execucao_rota (data, hora_inicio, hora_fim, distancia_percorrida_km,
           combustivel_consumido_l, volume_coletado_kg, id_rota, id_caminhao, id_motorista)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)""",
        (agora.strftime("%Y-%m-%d"), agora.strftime("%H:%M"), fim.strftime("%H:%M"),
         otim["km"], otim["litros"], round(volume, 2), id_rota),
    )


    for item in otim["ordem"]:
        sensor = con.execute("SELECT id_sensor FROM sensor_nivel WHERE id_conteiner = ?",
                             (item["id_conteiner"],)).fetchone()
        con.execute("INSERT INTO leitura_sensor (nivel_percentual, timestamp_leitura, id_sensor) VALUES (0, ?, ?)",
                    (agora.strftime(FORMATO_DATA), sensor["id_sensor"]))
    con.commit()
    return {"id_rota": id_rota, "pontos": len(otim["ordem"]), "km": otim["km"], "litros": otim["litros"]}



class Handler(BaseHTTPRequestHandler):
    def responder(self, dados, status=200):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        url = urlparse(self.path)
        try:
            if url.path == "/":
                with open(os.path.join(PASTA, "index.html"), "rb") as f:
                    corpo = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)
                return
            con = conectar()
            try:
                if url.path == "/api/conteineres":
                    self.responder(listar_conteineres(con))
                elif url.path == "/api/plano":
                    limite = float(parse_qs(url.query).get("limite", ["70"])[0])
                    self.responder(montar_plano(con, limite))
                elif url.path == "/api/historico":
                    self.responder(listar_historico(con))
                else:
                    self.responder({"erro": "Rota não encontrada"}, 404)
            finally:
                con.close()
        except Exception as erro:
            self.responder({"erro": str(erro)}, 500)

    def do_POST(self):
        url = urlparse(self.path)
        try:
            tamanho = int(self.headers.get("Content-Length", 0))
            corpo = json.loads(self.rfile.read(tamanho) or b"{}")
            con = conectar()
            try:
                if url.path == "/api/simular":
                    simular_leituras(con)
                    self.responder({"mensagem": "Novas leituras registradas."})
                elif url.path == "/api/executar":
                    self.responder(registrar_execucao(con, float(corpo.get("limite", 70))))
                else:
                    self.responder({"erro": "Rota não encontrada"}, 404)
            finally:
                con.close()
        except ValueError as erro:
            self.responder({"erro": str(erro)}, 400)
        except Exception as erro:
            self.responder({"erro": str(erro)}, 500)


if __name__ == "__main__":
    criar_banco()
    print("Servidor rodando em http://localhost:8000  (Ctrl+C para parar)")
    HTTPServer(("localhost", 8000), Handler).serve_forever()

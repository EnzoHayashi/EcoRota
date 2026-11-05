-- =====================================================================
-- Otimização de Rotas de Coleta de Lixo - Estrutura do banco (SQLite)
-- Baseado nas entidades definidas no Checkpoint 1.
-- Obs.: no SQLite a chave primária autoincrementada precisa ser INTEGER.
-- =====================================================================
PRAGMA foreign_keys = ON;

CREATE TABLE bairro (
    id_bairro  INTEGER PRIMARY KEY AUTOINCREMENT,
    nome       VARCHAR(100) NOT NULL,
    zona       VARCHAR(50)
);

CREATE TABLE ponto_coleta (
    id_ponto   INTEGER PRIMARY KEY AUTOINCREMENT,
    endereco   VARCHAR(150) NOT NULL,
    latitude   DECIMAL(9,6) NOT NULL,
    longitude  DECIMAL(9,6) NOT NULL,
    id_bairro  INT NOT NULL REFERENCES bairro(id_bairro)
);

CREATE TABLE tipo_residuo (
    id_tipo    INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao  VARCHAR(50) NOT NULL
);

CREATE TABLE conteiner (
    id_conteiner      INTEGER PRIMARY KEY AUTOINCREMENT,
    capacidade_litros DECIMAL(6,2) NOT NULL,
    id_ponto          INT NOT NULL REFERENCES ponto_coleta(id_ponto),
    id_tipo           INT NOT NULL REFERENCES tipo_residuo(id_tipo)
);

CREATE TABLE sensor_nivel (
    id_sensor        INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo           VARCHAR(50),
    data_instalacao  DATE,
    id_conteiner     INT NOT NULL REFERENCES conteiner(id_conteiner)
);

-- Tabela de maior volume: uma linha a cada leitura de cada sensor.
CREATE TABLE leitura_sensor (
    id_leitura         INTEGER PRIMARY KEY AUTOINCREMENT,
    nivel_percentual   DECIMAL(5,2) NOT NULL CHECK (nivel_percentual BETWEEN 0 AND 100),
    timestamp_leitura  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_sensor          INT NOT NULL REFERENCES sensor_nivel(id_sensor)
);
CREATE INDEX idx_leitura_sensor ON leitura_sensor(id_sensor, timestamp_leitura);

CREATE TABLE rota (
    id_rota                 INTEGER PRIMARY KEY AUTOINCREMENT,
    turno                   VARCHAR(20),
    dia_semana              VARCHAR(15),
    distancia_planejada_km  DECIMAL(6,2)
);

-- Associativa: resolve o N:M entre rota e ponto de coleta.
CREATE TABLE rota_ponto (
    id_rota      INT NOT NULL REFERENCES rota(id_rota),
    id_ponto     INT NOT NULL REFERENCES ponto_coleta(id_ponto),
    ordem_visita INT NOT NULL,
    PRIMARY KEY (id_rota, id_ponto)
);

CREATE TABLE caminhao (
    id_caminhao          INTEGER PRIMARY KEY AUTOINCREMENT,
    placa                VARCHAR(8) NOT NULL,
    capacidade_carga_kg  DECIMAL(8,2),
    consumo_medio_km_l   DECIMAL(5,2) NOT NULL
);

CREATE TABLE motorista (
    id_motorista  INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          VARCHAR(100) NOT NULL,
    cnh           VARCHAR(20)
);

-- Histórico de rotas realmente percorridas.
CREATE TABLE execucao_rota (
    id_execucao              INTEGER PRIMARY KEY AUTOINCREMENT,
    data                     DATE NOT NULL,
    hora_inicio              TIME,
    hora_fim                 TIME,
    distancia_percorrida_km  DECIMAL(6,2),
    combustivel_consumido_l  DECIMAL(6,2),
    volume_coletado_kg       DECIMAL(8,2),
    id_rota                  INT NOT NULL REFERENCES rota(id_rota),
    id_caminhao              INT NOT NULL REFERENCES caminhao(id_caminhao),
    id_motorista             INT NOT NULL REFERENCES motorista(id_motorista)
);

CREATE TABLE ocorrencia (
    id_ocorrencia  INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo           VARCHAR(50),
    descricao      TEXT,
    data_hora      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_ponto       INT NOT NULL REFERENCES ponto_coleta(id_ponto),
    id_execucao    INT REFERENCES execucao_rota(id_execucao)  -- opcional
);

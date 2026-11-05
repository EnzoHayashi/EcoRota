-- As leituras dos sensores e o histórico de execuções são gerados pelo server.py.

INSERT INTO bairro (id_bairro, nome, zona) VALUES
    (1, 'Bairro Leste A', 'Leste'),
    (2, 'Bairro Norte B', 'Norte'),
    (3, 'Bairro Centro C', 'Centro');

INSERT INTO tipo_residuo (id_tipo, descricao) VALUES
    (1, 'Orgânico'),
    (2, 'Reciclável');

INSERT INTO ponto_coleta (id_ponto, endereco, latitude, longitude, id_bairro) VALUES
    (1,  'Rua Exemplo 1, 100',   -23.565000, -46.523000, 1),
    (2,  'Rua Exemplo 2, 200',   -23.558000, -46.525000, 1),
    (3,  'Rua Exemplo 3, 300',   -23.556000, -46.530000, 1),
    (4,  'Rua Exemplo 4, 400',   -23.540000, -46.570000, 2),
    (5,  'Rua Exemplo 5, 500',   -23.545000, -46.575000, 2),
    (6,  'Rua Exemplo 6, 600',   -23.533000, -46.565000, 2),
    (7,  'Rua Exemplo 7, 700',   -23.550000, -46.590000, 3),
    (8,  'Rua Exemplo 8, 800',   -23.556000, -46.595000, 3),
    (9,  'Rua Exemplo 9, 900',   -23.560000, -46.585000, 3),
    (10, 'Rua Exemplo 10, 1000', -23.564000, -46.588000, 3),
    (11, 'Rua Exemplo 11, 1100', -23.540000, -46.560000, 2),
    (12, 'Rua Exemplo 12, 1200', -23.570000, -46.580000, 3);

-- Um contêiner (e um sensor) por ponto, para manter simples.
INSERT INTO conteiner (id_conteiner, capacidade_litros, id_ponto, id_tipo) VALUES
    (1, 1000, 1, 1),  (2, 1000, 2, 2),  (3, 660, 3, 1),   (4, 1000, 4, 2),
    (5, 1000, 5, 1),  (6, 660, 6, 2),   (7, 1000, 7, 1),  (8, 1000, 8, 2),
    (9, 660, 9, 1),   (10, 1000, 10, 2),(11, 1000, 11, 1),(12, 660, 12, 2);

INSERT INTO sensor_nivel (id_sensor, modelo, data_instalacao, id_conteiner) VALUES
    (1, 'UltraSense U1', '2026-06-01', 1),  (2, 'UltraSense U1', '2026-06-01', 2),
    (3, 'UltraSense U1', '2026-06-01', 3),  (4, 'UltraSense U1', '2026-06-01', 4),
    (5, 'UltraSense U1', '2026-06-01', 5),  (6, 'UltraSense U1', '2026-06-01', 6),
    (7, 'UltraSense U1', '2026-06-01', 7),  (8, 'UltraSense U1', '2026-06-01', 8),
    (9, 'UltraSense U1', '2026-06-01', 9),  (10, 'UltraSense U1', '2026-06-01', 10),
    (11, 'UltraSense U1', '2026-06-01', 11),(12, 'UltraSense U1', '2026-06-01', 12);

INSERT INTO caminhao (id_caminhao, placa, capacidade_carga_kg, consumo_medio_km_l) VALUES
    (1, 'ABC1D23', 8000, 2.50),
    (2, 'EFG4H56', 8000, 2.80);

INSERT INTO motorista (id_motorista, nome, cnh) VALUES
    (1, 'Motorista 1', '00000000001'),
    (2, 'Motorista 2', '00000000002');

-- Rota FIXA atual: visita TODOS os pontos, sempre na mesma ordem
-- (é a situação "antes" descrita no diagnóstico do Checkpoint 1).
INSERT INTO rota (id_rota, turno, dia_semana, distancia_planejada_km) VALUES
    (1, 'Manhã', 'Segunda', NULL);

INSERT INTO rota_ponto (id_rota, id_ponto, ordem_visita) VALUES
    (1, 1, 1),  (1, 7, 2),  (1, 4, 3),  (1, 10, 4), (1, 2, 5),  (1, 8, 6),
    (1, 5, 7),  (1, 11, 8), (1, 3, 9),  (1, 9, 10), (1, 6, 11), (1, 12, 12);

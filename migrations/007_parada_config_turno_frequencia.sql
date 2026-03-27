-- Rename nome → turno e adicionar frequencia_dias
ALTER TABLE parada_config RENAME COLUMN nome TO turno;
ALTER TABLE parada_config ALTER COLUMN turno DROP NOT NULL;
ALTER TABLE parada_config ADD COLUMN IF NOT EXISTS frequencia_dias TEXT;

-- Migrar tipos: ALMOCO → REFEICAO, INTERVALO → INTERVALO_1
UPDATE parada_config SET tipo = 'REFEICAO'    WHERE tipo = 'ALMOCO';
UPDATE parada_config SET tipo = 'INTERVALO_1' WHERE tipo = 'INTERVALO';

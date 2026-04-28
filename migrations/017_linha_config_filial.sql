ALTER TABLE linha_config ADD COLUMN IF NOT EXISTS filial VARCHAR(20) NOT NULL DEFAULT 'VTE';

UPDATE linha_config SET filial = 'VTT' WHERE setor = 'VTT';

DELETE FROM linha_config WHERE filial = 'VTT';

DELETE FROM linha_config
WHERE id NOT IN (
    SELECT MAX(id) FROM linha_config GROUP BY linha
);

ALTER TABLE linha_config DROP CONSTRAINT IF EXISTS linha_config_setor_linha_key;

ALTER TABLE linha_config ADD CONSTRAINT linha_config_linha_key UNIQUE (linha);

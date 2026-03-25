-- Recalcula produzido para OPs com fase_modelo = 'AMBAS'
-- O valor correto é LEAST(total_TOP, total_BOTTOM) dos apontamentos vinculados.
-- OPs sem nenhum apontamento ficam com produzido = 0.
UPDATE controle_ops co
SET produzido = COALESCE((
    SELECT LEAST(
        COALESCE(SUM(CASE WHEN a.fase = 'TOP'    THEN a.quantidade ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN a.fase = 'BOTTOM' THEN a.quantidade ELSE 0 END), 0)
    )
    FROM apontamento a
    WHERE a.op_id = co.id
), 0)
WHERE co.fase_modelo = 'AMBAS';

-- Migration 014: Adiciona coluna quantidade na tabela entrega (remessas parciais)
ALTER TABLE entrega ADD COLUMN IF NOT EXISTS quantidade INTEGER NOT NULL DEFAULT 0;

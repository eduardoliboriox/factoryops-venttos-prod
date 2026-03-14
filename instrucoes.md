1. Ajuste de organização e rota
   a página app/templates/estudo_tempo.html, bem como seu complemento app/templates/estudo_tempo_print.html pertencem a engenharia/, onde já tem a pagina app/templates/engenharia/folha_cronometragem.html.
   em relação a outras pastas/diretorios:
   funcionalidades/   app/templates/cadastro.html, app/templates/calcular.html, e app/templates/modelos.html, modelos.html tbm é de funcilidades porque é uma pagina que existe para cada respectivo setor dentro de funcionalidades/ , por exemplo hoje app/templates/modelos.html está para somente SMT, mas quando cadastrarem modelos IM/PA, PTH, VTT, cada uma vai ter o mesmo layout de app/templates/modelos.html, porem referente aos respectivos modelos cadastrados para aquele setor.
   produção/ já está ok (falta conteudo) 
   pcp/   já está ok (falta conteudo)

2. Com a mudança de nome para FactoryOps, eu já tinho instalado no meu celular o aplicativo com PWA, mas no celular ainda não está com o nome de FactoryOps, ainda estava SMT Manager, como eu não sabia o que fazer, eu desinstalei e instalei de novo, ai ficou com o nome correto. Contudo, eu tenho outros usuários com o app instalado, nao sei se vou ter que dizer pra todos desinstalarem e instalar de novo por causa da mudança de nome, tem como ajustar sem precisar notificalos.

3. Transcrição e descrição do documento Checklist de verificação de linha
   eu fiz transcrição de como é o documento real usado na fabrica, temos que fazer com o que a interface da pagina app/templates/producao/checklist_linha.html, possa fazer com o que determinado usuario que vai ser um operador de máquina possa usar o sistema para realização do documento de checklist que ele faz tudo de papel, ele vai poder fazer com o sistema, e para nós do sistema, a parte boa, vai ser que teremos a informação precisa de quando o operador realizou aquela determinada ação, mas a interface, precisa entender e atender a necessidade que temos varias linhas por setor, cada setor usa o checklist, a interface, o usuario primeiro vai logar no sistema (individual), depois ele vai na pagina de chelist e vai selecionar o setor (im,pa, smt, pth, vtt), depois de acordo com o setor, temos determinadas linhas, ele vai selecionar a linha dele, e vai fazer o o que ele tem que fazer no checkslits., apertar salvar, agora temos aquele chelist salvo, que ele pode selecionar facilmente, temos que ter uma especie de id, e na interface precisa constar data, que inicia com a data de hoje, NA INTERFACE precisa existe um botao de consultar checklist. para vermos chelist que forem de outra data, quando tivermos duvida, quando eu consultar um checklist de qualquer data, eu clicando na tela, eu tenho que poder ver a data,hora exata e qual user_name fez aquele chelists, na mesma linha tem dois operadores, entao , um vai verificar, depois o outro tbm, como um doublecheck pra evitar alimentação errada.
   o checklist de verificação de linha é realizado por lider, não operador, eu confundir, mas outros documentos é para operador.

# Descrição técnica completa do documento

**Checklist de Verificação da Linha — Venttos Electronics**

Este documento é um **formulário industrial de controle de processo**, utilizado para **verificação diária das linhas de produção SMT/SMD**.
O documento possui **frente e verso** e é impresso em **formato A4 paisagem**.

O layout é altamente estruturado, com **tabelas, colunas fixas, grid de controle diário e plano de ação para problemas encontrados**.

---

# 1 — Informações gerais do documento

Formato físico:

* Papel: **A4**
* Orientação: **Paisagem (landscape)**
* Impressão: **Preto e branco**
* Estrutura: **Tabela com múltiplas seções**
* Uso: **Controle operacional de linha de produção**

---

# 2 — Cabeçalho superior do documento

No topo da página existe uma linha de identificação do documento com o seguinte texto:

```
CÓPIA CONTROLADA PROIBIDO REPRODUZIR | Impresso por Casemiro Guerreiro | 02/03/2026 08:11:08 | Setor: MANUFATURA SMD
Ponto de distribuição: TODOS OS PROCESSOS | Responsável por receber: Casemiro Guerreiro
```

Este cabeçalho indica:

* Controle de versão
* Responsável pela impressão
* Data e hora
* Setor responsável
* Distribuição do documento

---

# 3 — Área de identificação da linha (lado direito da folha)

No lado **direito superior da folha**, existe um **bloco vertical de identificação do formulário**.

Esse bloco possui várias caixas de preenchimento.

### Logotipo

No topo deste bloco aparece:

```
Venttos
Electronics
```

Logotipo simples, alinhado à direita.

---

### Título do documento

Logo abaixo do logotipo está escrito:

```
CHECKLIST DE VERIFICAÇÃO DA LINHA
Lines Checklist Verification
```

Título bilíngue.

---

### Campos de identificação

Abaixo existem campos estruturados em caixas:

```
MODELO
Model

MÊS
Month

SETOR
Sector

LINHA
Line

RESPONSÁVEL
Responsible
```

Cada campo possui um espaço em branco para preenchimento manual.

---

# 4 — Área principal: “PONTOS A VERIFICAR”

No centro da folha existe uma **grande tabela vertical chamada**:

```
PONTOS A VERIFICAR
```

Essa tabela contém uma **lista numerada de itens de auditoria da linha**.

A estrutura da tabela é:

| ITEM | DESCRIÇÃO DO CHECK |
| ---- | ------------------ |

Os itens são numerados sequencialmente.

---

## Exemplos de itens que aparecem na lista

Os textos são perguntas de verificação operacional.

Alguns exemplos visíveis:

```
Todos os EPIs necessários estão disponíveis no ambiente de trabalho?
Existe identificação adequada dos equipamentos, das docas?
O ambiente está limpo e organizado?
A iluminação está adequada?
As ferramentas estão identificadas e organizadas?
Todos os postos de trabalho possuem instrução de trabalho atualizada?
Existe risco ergonômico identificado?
O operador possui treinamento adequado?
Os equipamentos estão em condições seguras de uso?
```

São perguntas de auditoria de processo.

A lista possui **dezenas de itens**.

---

# 5 — Grid de controle diário

Abaixo da lista de itens existe um **grande grid (grade)**.

Esse grid serve para registrar **verificações diárias durante o mês**.

Estrutura:

Colunas:

```
Dias do mês (Day of month)
```

São colunas numeradas:

```
1
2
3
4
5
...
até 31
```

Linhas:

Cada linha corresponde a um **item do checklist**.

---

### Como funciona o preenchimento

Para cada item e para cada dia:

O operador marca:

```
✓
OK
X
```

ou faz observação.

---

# 6 — Campo inferior de verificação

Na parte inferior da frente existe um pequeno bloco com campos como:

```
Realização
Check List Maker

Data
Check List Date
```

Área destinada à assinatura ou identificação de quem executou a verificação.

---

# 7 — Verso do documento

O verso é destinado a **registro de problemas e plano de ação**.

Esse lado possui uma **tabela grande chamada**:

```
PLANO DE AÇÃO
Action Plan
```

---

# 8 — Estrutura da tabela do plano de ação

A tabela possui as seguintes colunas:

| DIA | ITEM | PROBLEMA | CAUSA | AÇÃO | QUANDO? | RESPONSÁVEL | ASSINATURA | STATUS |

---

## Descrição das colunas

### DIA

Dia do mês em que o problema foi identificado.

---

### ITEM

Número do item do checklist que apresentou problema.

---

### PROBLEMA

Descrição do problema identificado.

Exemplo:

```
Ferramenta fora do padrão
Ausência de EPI
Falha na iluminação
```

---

### CAUSA

Causa raiz do problema.

Exemplo:

```
Falta de reposição
Erro de processo
Falta de manutenção
```

---

### AÇÃO

Ação corretiva definida.

Exemplo:

```
Substituir ferramenta
Treinar operador
Revisar iluminação
```

---

### QUANDO?

Prazo para execução da ação.

---

### RESPONSÁVEL

Pessoa responsável por executar a ação.

---

### ASSINATURA

Assinatura do responsável.

---

### STATUS

Estado da ação:

```
Aberto
Em andamento
Concluído
```

---

# 9 — Estrutura visual do verso

O verso é praticamente **uma grande tabela contínua** com muitas linhas para registro de ações.

As colunas ocupam toda a largura da folha.

---

# 10 — Objetivo do documento

Este documento tem como objetivo:

* Garantir **conformidade operacional da linha**
* Registrar **auditoria diária de processo**
* Identificar **desvios**
* Registrar **ações corretivas**

Ele funciona como:

```
Checklist + registro de problemas + plano de ação
```

---

# 11 — Uso típico na fábrica

Fluxo operacional:

1️⃣ Supervisor ou líder pega o checklist
2️⃣ Verifica cada item da linha
3️⃣ Marca o status no dia correspondente
4️⃣ Se houver problema, registra no verso
5️⃣ Define ação corretiva
6️⃣ Acompanha até resolução

---

# 12 — Resumo estrutural

Frente do documento:

```
Cabeçalho institucional
Identificação da linha
Lista de itens de verificação
Grid de controle diário
Campos de responsável
```

Verso do documento:

```
Tabela de plano de ação
Registro de problemas
Controle de responsáveis e status
```

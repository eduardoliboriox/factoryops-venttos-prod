from app.repositories import checklist_repository


def list_itens():
    return checklist_repository.list_itens()


def create_session_with_respostas(data: dict, respostas: list, user_id: int) -> int:
    sessao_id = checklist_repository.create_sessao({**data, "user_id": user_id})
    checklist_repository.create_respostas(sessao_id, respostas, user_id)
    return sessao_id


def create_plano_acao(data: dict):
    checklist_repository.create_plano_acao(data)


def get_sessao_detail(sessao_id: int):
    return checklist_repository.get_sessao_detail(sessao_id)


def list_sessoes(data_sessao=None, setor=None, linha=None, limit: int = 50):
    return checklist_repository.list_sessoes(data_sessao=data_sessao, setor=setor, linha=linha, limit=limit)

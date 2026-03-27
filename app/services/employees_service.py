from app.repositories.employees_repository import get_employee_by_matricula


def buscar_funcionario(matricula: str):
    """
    Autofill de funcionário (modo CREATE).

    Fonte da verdade:
    - employees (base histórica)
    - LEFT JOIN users + user_profiles (dados atuais)

    Retorna dados prontos para o frontend.
    """

    matricula = matricula.strip().lstrip("0")

    employee = get_employee_by_matricula(matricula)

    if not employee:
        return {"found": False}

    return {
        "found": True,
        "nome": employee.get("full_name"),
        "endereco": employee.get("endereco"),
        "telefone": employee.get("phone"),
    }

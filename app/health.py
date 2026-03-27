from app import create_app

def run_health_check():

    app = create_app()

    assert app is not None, "Falha ao criar aplicação"

    required_configs = [
        "SECRET_KEY",
        "DATABASE_URL",
        "ENVIRONMENT"
    ]

    for config in required_configs:
        assert app.config.get(config), f"{config} não configurado"

    return True

if __name__ == "__main__":
    run_health_check()
    print("✔ Application health check passed")

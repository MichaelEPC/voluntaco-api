"""Tests de autorización en los endpoints de fundaciones (/api/v1/fundaciones)."""

PREFIX = "/api/v1/fundaciones"


def test_eliminar_voluntariado_requiere_rol_fundacion(client, auth_token_factory):
    # role=1 => voluntario, no tiene permiso para eliminar voluntariados
    token = auth_token_factory(role=1)

    response = client.delete(
        f"{PREFIX}/voluntariados/eliminar/1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Solo las fundaciones pueden realizar esta acción."


def test_eliminar_voluntariado_sin_token(client):
    response = client.delete(f"{PREFIX}/voluntariados/eliminar/1")

    assert response.status_code == 401

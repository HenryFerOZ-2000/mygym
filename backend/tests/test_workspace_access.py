import uuid


def test_only_active_authorized_workspaces_are_discovered(signed_api, workspaces):
    a, b, outsider = workspaces
    response = signed_api.get("/api/v1/me/workspaces/")
    assert response.status_code == 200
    assert {w["id"] for w in response.json()} == {str(a.id), str(b.id)}
    a.is_active = False
    a.save()
    assert {w["id"] for w in signed_api.get("/api/v1/me/workspaces/").json()} == {
        str(b.id)
    }


def test_revocation_and_capability_change_apply_next_request(signed_api, workspaces):
    from modules.workspaces.models import WorkspaceAccess, WorkspaceCapability

    a = workspaces[0]
    url = f"/api/v1/workspaces/{a.id}/clients/"
    assert signed_api.get(url).status_code == 200
    WorkspaceCapability.objects.filter(workspace=a).update(enabled=False)
    assert signed_api.get(url).status_code == 403
    WorkspaceCapability.objects.filter(workspace=a).update(enabled=True)
    WorkspaceAccess.objects.filter(workspace=a).update(is_active=False)
    assert signed_api.get(url).status_code == 404


def test_coach_denied_reception_allowed(signed_api, workspaces):
    from modules.workspaces.models import WorkspaceAccess

    a = workspaces[0]
    url = f"/api/v1/workspaces/{a.id}/clients/"
    WorkspaceAccess.objects.filter(workspace=a).update(role="COACH")
    assert signed_api.get(url).status_code == 403
    WorkspaceAccess.objects.filter(workspace=a).update(role="RECEPTION")
    assert signed_api.get(url).status_code == 200


def test_unauthorized_and_missing_workspace_indistinguishable(signed_api, workspaces):
    responses = [
        signed_api.get(f"/api/v1/workspaces/{value}/clients/")
        for value in [workspaces[2].id, uuid.uuid4()]
    ]
    assert all(r.status_code == 404 for r in responses)
    assert responses[0].json() == responses[1].json()

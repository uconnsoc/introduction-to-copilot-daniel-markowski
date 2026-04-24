"""Tests for activity endpoints using AAA (Arrange-Act-Assert) pattern"""
import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client: TestClient):
        """Test that all activities are returned with correct structure"""
        # Arrange
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class",
            "Basketball Team", "Soccer Club", "Art Studio",
            "Music Band", "Debate Team", "Science Club"
        ]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert all(activity in activities for activity in expected_activities)
        assert len(activities) == 9

    def test_activity_has_required_fields(self, client: TestClient):
        """Test that each activity has all required fields"""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            assert required_fields.issubset(activity_data.keys()), \
                f"Activity '{activity_name}' missing required fields"
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)

    def test_activity_participants_are_emails(self, client: TestClient):
        """Test that participants are valid email strings"""
        # Arrange & Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant, \
                    f"Invalid email format for participant in {activity_name}"


class TestSignup:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_succeeds(self, client: TestClient):
        """Test successful signup for a new participant"""
        # Arrange
        activity = "Chess Club"
        email = "new_student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}",
            headers={"content-length": "0"}
        )

        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]

    def test_signup_nonexistent_activity_returns_404(self, client: TestClient):
        """Test signup fails for non-existent activity"""
        # Arrange
        activity = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}",
            headers={"content-length": "0"}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_participant_returns_400(self, client: TestClient):
        """Test signup fails when participant already registered"""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Already registered

        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}",
            headers={"content-length": "0"}
        )

        # Assert
        assert response.status_code == 400
        assert "Already registered" in response.json()["detail"]

    def test_signup_with_special_characters_in_email(self, client: TestClient):
        """Test signup with email containing special characters"""
        # Arrange
        activity = "Art Studio"
        email = "student_test@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}",
            headers={"content-length": "0"}
        )

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]


class TestUnregister:
    """Test suite for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant_succeeds(self, client: TestClient):
        """Test successful unregistration of an existing participant"""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Already registered

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}",
            headers={"content-length": "0"}
        )

        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_nonexistent_activity_returns_404(self, client: TestClient):
        """Test unregister fails for non-existent activity"""
        # Arrange
        activity = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}",
            headers={"content-length": "0"}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_unregistered_participant_returns_400(self, client: TestClient):
        """Test unregister fails when participant not registered"""
        # Arrange
        activity = "Chess Club"
        email = "not_registered@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}",
            headers={"content-length": "0"}
        )

        # Assert
        assert response.status_code == 400
        assert "Not registered" in response.json()["detail"]

    def test_unregister_then_signup_succeeds(self, client: TestClient):
        """Test that after unregistering, participant can sign up again"""
        # Arrange
        activity = "Basketball Team"
        email = "james@mergington.edu"

        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}",
            headers={"content-length": "0"}
        )

        # Act - Sign up again
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}",
            headers={"content-length": "0"}
        )

        # Assert
        assert unregister_response.status_code == 200
        assert signup_response.status_code == 200


class TestActivityCapacity:
    """Test suite for activity capacity constraints"""

    def test_get_participants_count(self, client: TestClient):
        """Test that participant count is accurate"""
        # Arrange & Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            participant_count = len(activity_data["participants"])
            max_participants = activity_data["max_participants"]
            assert participant_count <= max_participants, \
                f"{activity_name} has more participants than max capacity"

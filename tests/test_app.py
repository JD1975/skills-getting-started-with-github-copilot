"""
Tests for the FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestRootRoute:
    """Test the root route"""
    
    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Check that activities is a dict
        assert isinstance(activities, dict)
        
        # Check for expected activities
        expected_activities = [
            "Basketball Team",
            "Tennis Club",
            "Art Studio",
            "Drama Club",
            "Debate Team",
            "Robotics Club",
            "Chess Club",
            "Programming Class",
            "Gym Class"
        ]
        
        for activity_name in expected_activities:
            assert activity_name in activities
    
    def test_activity_structure(self):
        """Test that each activity has the required structure"""
        response = client.get("/activities")
        activities = response.json()
        
        for name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)


class TestSignup:
    """Test the signup endpoint"""
    
    def test_signup_successful(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball%20Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "newstudent@mergington.edu" in result["message"]
        assert "Basketball Team" in result["message"]
        
        # Verify participant was added
        activities = client.get("/activities").json()
        assert "newstudent@mergington.edu" in activities["Basketball Team"]["participants"]
    
    def test_signup_duplicate_activity(self):
        """Test that a student cannot sign up for multiple activities"""
        # First signup
        response1 = client.post(
            "/activities/Tennis%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Try to signup for another activity
        response2 = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        result = response2.json()
        assert "already signed up" in result["detail"]
    
    def test_signup_activity_not_found(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"]


class TestUnregister:
    """Test the unregister endpoint"""
    
    def test_unregister_successful(self):
        """Test successful unregister from an activity"""
        # First get an activity with participants
        response = client.get("/activities")
        activities = response.json()
        
        # Use an existing participant
        activity_name = "Basketball Team"
        participant = activities[activity_name]["participants"][0]
        
        # Unregister the participant
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={participant}"
        )
        assert response.status_code == 200
        result = response.json()
        assert "Unregistered" in result["message"]
        assert participant in result["message"]
        
        # Verify participant was removed
        activities = client.get("/activities").json()
        assert participant not in activities[activity_name]["participants"]
    
    def test_unregister_activity_not_found(self):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"]
    
    def test_unregister_participant_not_registered(self):
        """Test unregister of non-registered participant"""
        response = client.delete(
            "/activities/Basketball%20Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "not registered" in result["detail"]


class TestActivityAvailability:
    """Test activity availability tracking"""
    
    def test_spots_left_calculation(self):
        """Test that spots left is calculated correctly"""
        response = client.get("/activities")
        activities = response.json()
        
        for name, details in activities.items():
            spots_left = details["max_participants"] - len(details["participants"])
            assert spots_left >= 0
            assert spots_left <= details["max_participants"]

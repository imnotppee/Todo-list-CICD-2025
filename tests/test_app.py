import pytest
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError
from app import create_app
from app.models import db, Todo


# -------------------- 🔧 Fixtures --------------------
@pytest.fixture
def app():
    """Create and configure a test app instance"""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner"""
    return app.test_cli_runner()


# =====================================================
# 🧩 1.1 TestAppFactory
# =====================================================
class TestAppFactory:
    """Test application factory and configuration"""

    def test_app_creation(self, app):
        """Test app is created successfully"""
        assert app is not None
        assert app.config['TESTING'] is True

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info"""
        response = client.get('/')
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'version' in data
        assert 'endpoints' in data

    def test_404_error_handler(self, client):
        """Test 404 error handler"""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data

    def test_exception_handler(self, app):
        """Test generic exception handler"""
        # ปิด TESTING mode ชั่วคราว
        app.config['TESTING'] = False

        @app.route('/test-error')
        def trigger_error():
            raise Exception('Test error')

        # ทดสอบ
        with app.test_client() as test_client:
            response = test_client.get('/test-error')
            assert response.status_code == 500
            assert 'Internal server error' in response.get_json()['error']

        # เปิด TESTING mode กลับ
        app.config['TESTING'] = True


# =====================================================
# 🩺 1.2 TestHealthCheck
# =====================================================
class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_endpoint_success(self, client):
        """Test health check returns 200 when database is healthy"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['database'] == 'connected'

    @patch('app.routes.db.session.execute')
    def test_health_endpoint_database_error(self, mock_execute, client):
        """Test health check returns 503 when database is down"""
        mock_execute.side_effect = Exception('Database connection failed')

        response = client.get('/api/health')
        assert response.status_code == 503
        data = response.get_json()
        assert data['status'] == 'unhealthy'
        assert data['database'] == 'disconnected'
        assert 'error' in data


# =====================================================
# 🧱 1.3 TestTodoModel
# =====================================================
class TestTodoModel:
    """Test Todo model methods"""

    def test_todo_to_dict(self, app):
        """Test todo model to_dict method"""
        with app.app_context():
            todo = Todo(title='Test Todo', description='Test Description')
            db.session.add(todo)
            db.session.commit()

            todo_dict = todo.to_dict()
            assert todo_dict['title'] == 'Test Todo'
            assert todo_dict['description'] == 'Test Description'
            assert todo_dict['completed'] is False
            assert 'id' in todo_dict
            assert 'created_at' in todo_dict
            assert 'updated_at' in todo_dict

    def test_todo_repr(self, app):
        """Test todo model __repr__ method"""
        with app.app_context():
            todo = Todo(title='Test Todo')
            db.session.add(todo)
            db.session.commit()

            repr_str = repr(todo)
            assert 'Todo' in repr_str
            assert 'Test Todo' in repr_str


# =====================================================
# 📦 1.4 TestTodoAPI
# =====================================================
class TestTodoAPI:
    """Test Todo CRUD operations"""

    def test_get_empty_todos(self, client):
        """Test getting todos when database is empty"""
        response = client.get('/api/todos')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 0
        assert data['data'] == []

    def test_create_todo_with_full_data(self, client):
        """Test creating a new todo with title and description"""
        todo_data = {'title': 'Test Todo', 'description': 'This is a test todo'}
        response = client.post('/api/todos', json=todo_data)
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['title'] == 'Test Todo'
        assert data['data']['description'] == 'This is a test todo'
        assert data['data']['completed'] is False
        assert 'message' in data

    def test_create_todo_with_title_only(self, client):
        """Test creating todo with only title (description is optional)"""
        todo_data = {'title': 'Test Todo Only Title'}
        response = client.post('/api/todos', json=todo_data)
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['title'] == 'Test Todo Only Title'
        assert data['data']['description'] == ''

    def test_create_todo_without_title(self, client):
        """Test creating todo without title fails validation"""
        response = client.post('/api/todos', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Title is required' in data['error']

    @patch('app.routes.db.session.commit')
    def test_create_todo_database_error(self, mock_commit, client):
        """Test database error during todo creation"""
        mock_commit.side_effect = SQLAlchemyError('Database error')
        response = client.post('/api/todos', json={'title': 'Test'})
        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data

    def test_update_todo_database_error(self, client, app):
        """Test database error during todo update"""
        # 1️⃣ สร้าง todo ตัวจริงก่อน
        with app.app_context():
            todo = Todo(title='Test')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        # 2️⃣ Mock commit หลังจากสร้างเสร็จ
        with app.app_context():
            with patch('app.routes.db.session.commit', side_effect=SQLAlchemyError('Database error')):
                response = client.put(f'/api/todos/{todo_id}', json={'title': 'New'})
                assert response.status_code == 500
                data = response.get_json()
                assert data['success'] is False
                assert 'error' in data


# =====================================================
# 🔗 1.5 TestIntegration
# =====================================================
class TestIntegration:
    """Integration tests for complete workflows"""

    def test_complete_todo_lifecycle(self, client):
        """Test complete CRUD workflow"""
        # Create
        create_response = client.post('/api/todos', json={
            'title': 'Integration Test Todo',
            'description': 'Testing full lifecycle'
        })
        assert create_response.status_code == 201
        todo_id = create_response.get_json()['data']['id']

        # Read
        read_response = client.get(f'/api/todos/{todo_id}')
        assert read_response.status_code == 200
        assert read_response.get_json()['data']['title'] == 'Integration Test Todo'

        # Update
        update_response = client.put(f'/api/todos/{todo_id}', json={
            'title': 'Updated Integration Test',
            'completed': True
        })
        assert update_response.status_code == 200
        updated_data = update_response.get_json()['data']
        assert updated_data['title'] == 'Updated Integration Test'
        assert updated_data['completed'] is True

        # Delete
        delete_response = client.delete(f'/api/todos/{todo_id}')
        assert delete_response.status_code == 200

        # Verify deletion
        verify_response = client.get(f'/api/todos/{todo_id}')
        assert verify_response.status_code == 404

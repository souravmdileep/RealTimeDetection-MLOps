pipeline {
    agent any

    environment {
        // YOUR DOCKERHUB USERNAME
        DOCKERHUB_USER = "souravmdileep"
        
        // Image Names
        BACKEND_IMAGE = "${DOCKERHUB_USER}/backend"
        FRONTEND_IMAGE = "${DOCKERHUB_USER}/frontend"
        ALERT_IMAGE = "${DOCKERHUB_USER}/alert-service"
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo "🚀 Starting Pipeline..."
                checkout scm
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                echo "🐳 Building Images first (Saves RAM)..."
                
                # Build Backend (Heavy)
                docker build -t $BACKEND_IMAGE:test -f docker/backend.Dockerfile .
                
                # Build Frontend
                docker build -t $FRONTEND_IMAGE:test -f docker/frontend.Dockerfile .
                
                # Build Alert Service
                docker build -t $ALERT_IMAGE:test -f docker/alert.Dockerfile .
                '''
            }
        }

        stage('Test Environment Setup') {
            steps {
                sh '''
                echo "🛠️ Setting up lightweight test env..."
                python3 -m venv venv
                . venv/bin/activate
                
                # We ONLY install requests, NOT the heavy ML libs
                # The heavy stuff is already inside the Docker container!
                pip install requests
                '''
            }
        }

        stage('Integration Testing') {
            steps {
                script {
                    try {
                        echo "🏥 Starting Temporary Test Container..."
                        // Run the backend we just built on a test port
                        sh 'docker run -d -p 8085:8000 --name ci-test-backend $BACKEND_IMAGE:test'
                        
                        // Wait for it to boot (Heavy models take time)
                        sleep 15
                        
                        echo "🧪 Running Health Check..."
                        sh 'curl -f http://localhost:8085/health'

                        echo "📉 Running Drift Detection..."
                        // We override the URL to point to our test container port 8085
                        // Modify
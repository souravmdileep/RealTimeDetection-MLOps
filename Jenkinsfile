pipeline {
    agent any

    environment {
        DOCKERHUB_USER = "souravmdileep"
        
        // Define target names for Docker Hub
        BACKEND_IMAGE_HUB = "${DOCKERHUB_USER}/backend"
        FRONTEND_IMAGE_HUB = "${DOCKERHUB_USER}/frontend"
        ALERT_IMAGE_HUB = "${DOCKERHUB_USER}/alert-service"
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo "Starting Pipeline..."
                checkout scm
            }
        }

        stage('Build & Prepare Images') {
            steps {
                script {
                    // Build Alert Service
                    echo "Building Alert Service..."
                    docker.build("${ALERT_IMAGE_HUB}:latest", "-f docker/alert.Dockerfile .")
                    
                    // Build Frontend
                    echo "Building Frontend..."
                    docker.build("${FRONTEND_IMAGE_HUB}:latest", "-f docker/frontend.Dockerfile .")
                    
                    // 3. BACKEND: Build from source (Required to apply code fixes)
                    echo "Building Backend..."
                    
                    // We try to pull first to use it as a cache source (speeds up build), 
                    // but we MUST run 'build' to apply your new app.py changes.
                    sh """
                        docker pull ${BACKEND_IMAGE_HUB}:latest || true
                        docker build \
                            --cache-from ${BACKEND_IMAGE_HUB}:latest \
                            -t ${BACKEND_IMAGE_HUB}:latest \
                            -f docker/backend.Dockerfile .
                    """
                }
            }
        }

        stage('Test Environment Setup') {
            steps {
                sh '''
                echo "Setting up lightweight test env..."
                python3 -m venv venv
                . venv/bin/activate
                pip install requests
                '''
            }
        }

        stage('Integration Testing') {
            steps {
                script {
                    try {
                        echo "Starting Full Stack via Docker Compose..."
                        // This creates images named: mlops-pipeline-backend, mlops-pipeline-frontend
                        sh 'docker compose up -d'
                        
                        echo "Waiting 30s for services to stabilize..."
                        sleep 30
                        
                        echo "Running Health Check..."
                        sh 'curl -f http://localhost:8000/health'

                        echo "Running Drift Detection..."
                        sh '''
                        . venv/bin/activate
                        python3 scripts/drift_detection.py || true
                        '''
                    } finally {
                        echo "Cleaning up Test Environment..."
                        sh 'docker compose down'
                    }
                }
            }
        }

        stage('Push to DockerHub') {
            steps {
                echo "Pushing Verified Images..."
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'D_USER', passwordVariable: 'D_PASS')]) {
                    sh '''
                    echo "$D_PASS" | docker login -u "$D_USER" --password-stdin
                    
                    # Tag the Compose-built images to Docker Hub names
                    # Note: Using 'mlops-pipeline' prefix based on your previous logs
                    
                    docker tag mlops-pipeline-backend:latest ${BACKEND_IMAGE_HUB}:latest
                    docker tag mlops-pipeline-frontend:latest ${FRONTEND_IMAGE_HUB}:latest
                    docker tag mlops-pipeline-alert-service:latest ${ALERT_IMAGE_HUB}:latest
                    
                    docker push ${BACKEND_IMAGE_HUB}:latest
                    docker push ${FRONTEND_IMAGE_HUB}:latest
                    docker push ${ALERT_IMAGE_HUB}:latest
                    '''
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo "Pipeline SUCCESS. Images are live."
        }
        failure {
            echo "Pipeline FAILED."
        }
    }
}
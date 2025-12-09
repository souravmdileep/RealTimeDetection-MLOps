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

        stage('Build & Prepare Images') {
            steps {
                script {
                    // 1. ALERT SERVICE: Build from source (Fast)
                    echo "Building Alert Service..."
                    docker.build("$ALERT_IMAGE:latest", "-f docker/alert.Dockerfile .")
                    
                    // 2. FRONTEND: Build from source (Medium - proves Web Ops)
                    echo "Building Frontend..."
                    docker.build("$FRONTEND_IMAGE:latest", "-f docker/frontend.Dockerfile .")
                    
                    // 3. BACKEND: Pull optimized artifact (Heavy ML - Saves 2GB RAM/Bandwidth)
                    echo "Pulling Pre-Optimized ML Backend..."
                    sh """
                        docker pull $BACKEND_IMAGE:latest
                        # Retag it so the next stages (Push) recognize it
                        docker tag $BACKEND_IMAGE:latest $BACKEND_IMAGE:test
                    """
                }
            }
        }

        stage('Test Environment Setup') {
            steps {
                sh '''
                echo "🛠️ Setting up lightweight test env..."
                python3 -m venv venv
                . venv/bin/activate
                
                # We ONLY install requests, NOT the heavy ML libs
                pip install requests
                '''
            }
        }

        stage('Integration Testing') {
            steps {
                script {
                    try {
                        echo "🏥 Starting Full Stack via Docker Compose..."
                        // We use the docker-compose.yml we already wrote!
                        // It spins up Backend + Alert Service + Frontend
                        sh 'docker compose up -d'
                        
                        echo "⏳ Waiting 30s for services to stabilize..."
                        sleep 30
                        
                        echo "🧪 Running Health Check..."
                        // Note: In Jenkins, localhost works because we are on the host network
                        sh 'curl -f http://localhost:8000/health'

                        echo "📉 Running Drift Detection..."
                        sh '''
                        . venv/bin/activate
                        python3 scripts/drift_detection.py || true
                        '''
                    } finally {
                        echo "🧹 Cleaning up Test Environment..."
                        sh 'docker compose down'
                    }
                }
            }
        }

        stage('Push to DockerHub') {
            steps {
                echo "🚀 Pushing Verified Images..."
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'D_USER', passwordVariable: 'D_PASS')]) {
                    sh '''
                    echo "$D_PASS" | docker login -u "$D_USER" --password-stdin
                    
                    # Retag for latest and push
                    docker tag $BACKEND_IMAGE:test $BACKEND_IMAGE:latest
                    docker tag $FRONTEND_IMAGE:test $FRONTEND_IMAGE:latest
                    docker tag $ALERT_IMAGE:test $ALERT_IMAGE:latest
                    
                    docker push $BACKEND_IMAGE:latest
                    docker push $FRONTEND_IMAGE:latest
                    docker push $ALERT_IMAGE:latest
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
            echo "✅ Pipeline SUCCESS! Images are live."
        }
        failure {
            echo "❌ Pipeline FAILED."
        }
    }
}
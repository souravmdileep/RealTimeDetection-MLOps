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
                pip install requests
                '''
            }
        }

        stage('Integration Testing') {
            steps {
                script {
                    try {
                        echo "🏥 Starting Temporary Test Container..."
                        // Run the backend we just built on a test port 8085
                        sh 'docker run -d -p 8085:8000 --name ci-test-backend $BACKEND_IMAGE:test'
                        
                        echo "⏳ Waiting 20s for backend to boot..."
                        sleep 20
                        
                        echo "🧪 Running Health Check..."
                        sh 'curl -f http://localhost:8085/health'

                        echo "📉 Running Drift Detection..."
                        sh '''
                        . venv/bin/activate
                        # Temporarily point script to test port 8085
                        sed -i "s|localhost:8000|localhost:8085|g" scripts/drift_detection.py
                        
                        # Run script (allow failure with || true)
                        python3 scripts/drift_detection.py || true
                        
                        # Revert script change
                        sed -i "s|localhost:8085|localhost:8000|g" scripts/drift_detection.py
                        '''
                    } finally {
                        echo "🧹 Cleaning up Test Container..."
                        sh 'docker stop ci-test-backend || true'
                        sh 'docker rm ci-test-backend || true'
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
pipeline {
    agent any

    environment {
        
        DOCKERHUB_USER = "souravmdileep" 
        
        // Define Image Names
        BACKEND_IMAGE = "${DOCKERHUB_USER}/backend"
        FRONTEND_IMAGE = "${DOCKERHUB_USER}/frontend"
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo "Starting Pipeline..."
                checkout scm
            }
        }

        stage('Setup Environment') {
            steps {
                sh '''
                echo "Setting up Virtual Environment..."
                # Create a fresh venv for testing
                python3 -m venv venv
                . venv/bin/activate
                
                # Install dependencies
                pip install --upgrade pip
                pip install -r backend/requirements.txt
                '''
            }
        }

        stage('Backend Health Check') {
            steps {
                script {
                    echo "Checking System Health..."
                    // 1. Start the backend in the background (nohup)
                    // We direct logs to a file so it doesn't clutter Jenkins console
                    sh 'nohup venv/bin/uvicorn backend.app:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &'
                    
                    // 2. Wait 10 seconds for it to boot up
                    sleep 10
                    
                    // 3. Hit the health endpoint
                    sh 'curl -f http://127.0.0.1:8000/health'
                }
            }
        }

        stage('Drift Detection') {
            steps {
                sh '''
                echo "Checking for Model Drift..."
                . venv/bin/activate
                
                # Run the drift script against the test images
                # We add "|| true" so drift warnings don't stop the build
                python3 scripts/drift_detection.py || true
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                echo "Building Backend Image..."
                docker build -t $BACKEND_IMAGE:latest -f docker/backend.Dockerfile .
                
                echo "Building Frontend Image..."
                docker build -t $FRONTEND_IMAGE:latest -f docker/frontend.Dockerfile .
                '''
            }
        }

        stage('Push to DockerHub') {
            steps {
                echo "Pushing to Docker Hub..."
                // Use the credentials ID we created in Step 7B
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'D_USER', passwordVariable: 'D_PASS')]) {
                    sh '''
                    echo "$D_PASS" | docker login -u "$D_USER" --password-stdin
                    docker push $BACKEND_IMAGE:latest
                    docker push $FRONTEND_IMAGE:latest
                    '''
                }
            }
        }
    }

    post {
        always {
            echo "Cleaning up..."
            // Kill the background uvicorn process
            sh 'pkill -f uvicorn || true'
            // Clean workspace to save space
            cleanWs()
        }
        success {
            echo "Pipeline SUCCESS! Images are live on Docker Hub."
        }
        failure {
            echo "Pipeline FAILED. Check logs."
        }
    }
}
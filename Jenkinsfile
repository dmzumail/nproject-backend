pipeline {
    agent any

    environment {
        MANIFESTS_REPO = "https://github.com/dmzumail/k8s-manifests.git"
        REGISTRY = "85.208.87.35:5000" 
        IMAGE_NAME = "nproject-backend"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        FULL_IMAGE = "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Проверка кода...'
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Создание image: ${FULL_IMAGE}"
                sh "docker build -t ${FULL_IMAGE} ."
            }
        }

        stage('Push to Registry') {
            steps {
                echo "Pushing image..."
                sh "docker push ${FULL_IMAGE}"
            }
        }

        stage('Update GitOps Manifests') {
            steps {
                echo 'Обновление k8s manifests...'
                script {
                    dir('k8s-temp') {
                        git url: MANIFESTS_REPO
                        sh """
                            sed -i 's|image: .*|image: ${FULL_IMAGE}|g' deployment.yaml
                        """
                        
                        sh """
                            git config user.email "jenkins@nproject.local"
                            git config user.name "Jenkins CI"
                            git add prod/deployment.yaml
                            git commit -m "Auto-update: Bump image to ${IMAGE_TAG}" || echo "No changes to commit"
                            git push origin main
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            sh 'rm -rf k8s-temp'
            sh 'docker image prune -f'
        }
    }
}
pipeline {
    agent any

    environment {
        MANIFESTS_REPO = "https://github.com/dmzumail/k8s-manifests.git"
        REGISTRY = "85.208.87.35:5000" 
        IMAGE_NAME = "nproject-backend"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        FULL_IMAGE = "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

        GITHUB_CREDS_ID = 'github-creds'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Проверка кода...'
                git url: 'https://github.com/dmzumail/nproject-backend.git', 
                    credentialsId: GITHUB_CREDS_ID
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
                echo "Пушинг image в локальный репозиторий..."
                sh "docker push ${FULL_IMAGE}"
            }
        }

        stage('Update GitOps Manifests') {
            steps {
                echo 'Обновление k8s manifests в Git...'
                script {
                    dir('k8s-temp') {
                        git url: MANIFESTS_REPO, credentialsId: GITHUB_CREDS_ID
                        
                        sh """
                            sed -i 's|image: .*|image: ${FULL_IMAGE}|g' prod/deployment.yaml
                        """
                        
                        sh """
                            git config user.email "jenkins@nproject.local"
                            git config user.name "Jenkins CI Bot"
                            git add prod/deployment.yaml
                            git commit -m "Auto-update: Bump image to ${IMAGE_TAG}" || echo "Нет изменений в коммите"
                            
                            withCredentials([usernamePassword(credentialsId: GITHUB_CREDS_ID, usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                                sh "git push https://${GIT_USER}:${GIT_PASS}@github.com/dmzumail/k8s-manifests.git main"
                            }
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
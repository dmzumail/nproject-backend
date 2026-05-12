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
                echo 'Checking out code...'
                git url: 'https://github.com/dmzumail/nproject-backend.git', 
                    branch: 'main',
                    credentialsId: GITHUB_CREDS_ID
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building image: ${FULL_IMAGE}"
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
                echo 'Updating k8s manifests...'
                dir('k8s-temp') {
                    git url: MANIFESTS_REPO, 
                        branch: 'main',
                        credentialsId: GITHUB_CREDS_ID
                    
                    sh """
                        sed -i 's|image: .*|image: ${FULL_IMAGE}|g' apps/nproject/nproject-backend.yaml
                    """
                    
                    sh 'git config user.email "jenkins@nproject.local"'
                    sh 'git config user.name "Jenkins CI Bot"'
                    sh "git add apps/nproject/nproject-backend.yaml"
                    sh "git commit -m 'Auto-update: Bump image to ${IMAGE_TAG}' || echo 'No changes to commit'"
                    
                    withCredentials([usernamePassword(credentialsId: GITHUB_CREDS_ID, usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                        sh 'git push https://${GIT_USER}:${GIT_PASS}@github.com/dmzumail/k8s-manifests.git main'
                    }
                }
            }
        }
    }
    
    post {
        always {
            echo 'Build finished.'
            sh 'rm -rf k8s-temp || true'
        }
    }
}
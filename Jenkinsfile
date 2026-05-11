pipeline {
    agent {
        kubernetes {
            inheritFrom 'docker-agent'
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: docker
    image: docker:cli
    command: ["cat"]
    tty: true
    volumeMounts:
    - name: docker-socket
      mountPath: "/var/run/docker.sock"
  volumes:
  - name: docker-socket
    hostPath:
      path: "/var/run/docker.sock"
'''
        }
    }

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
                container('docker') {
                    echo "Building image: ${FULL_IMAGE}"
                    sh "docker build -t ${FULL_IMAGE} ."
                }
            }
        }

        stage('Push to Registry') {
            steps {
                container('docker') {
                    echo "Pushing image..."
                    sh "docker push ${FULL_IMAGE}"
                }
            }
        }

        stage('Update GitOps Manifests') {
            steps {
                echo 'Updating k8s manifests...'
                script {
                    container('docker') {
                        dir('k8s-temp') {
                            git url: MANIFESTS_REPO, 
                                branch: 'main',
                                credentialsId: GITHUB_CREDS_ID
                            
                            sh """
                                sed -i "s|image: ${REGISTRY}/${IMAGE_NAME}:.*|image: ${FULL_IMAGE}|g" prod/deployment.yaml
                            """
                            
                            withCredentials([usernamePassword(credentialsId: GITHUB_CREDS_ID, usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                                sh """
                                    git config user.email "jenkins@nproject.local"
                                    git config user.name "Jenkins CI Bot"
                                    git add prod/deployment.yaml
                                    git commit -m "Auto-update: Bump image to ${IMAGE_TAG}" || echo "No changes to commit"
                                    git push https://${GIT_USER}:${GIT_PASS}@github.com/dmzumail/k8s-manifests.git main
                                """
                            }
                        }
                    }
                }
            }
        }
    }
    
    post {
        always {
            echo 'Build finished. Agent pod will be deleted automatically.'
        }
    }
}
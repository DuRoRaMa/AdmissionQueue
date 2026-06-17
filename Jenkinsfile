properties([
    pipelineTriggers([
        githubPush()
    ])
])

pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        DEPLOY_DIR = '/opt/admission-queue'
        BACKEND_DIR = '/opt/admission-queue/AdmissionQueue'
        FRONTEND_DIR = '/opt/admission-queue/AdmissionQueueWeb'
        FRONTEND_REPO = 'https://github.com/DuRoRaMa/AdmissionQueueWeb.git'
        COMPOSE_FILE = 'docker-compose.prod.yml'
        ENV_FILE = '.env.prod'
    }

    stages {
        stage('Check branch') {
            steps {
                script {
                    if (env.BRANCH_NAME && env.BRANCH_NAME != 'main') {
                        currentBuild.result = 'NOT_BUILT'
                        error('Deploy is allowed only from main branch')
                    }
                }
            }
        }

        stage('Prepare directories') {
            steps {
                sh '''
                    set -e
                    mkdir -p "$DEPLOY_DIR"
                    mkdir -p "$BACKEND_DIR"
                '''
            }
        }

        stage('Sync backend') {
            steps {
                sh '''
                    set -e
                    rsync -a --delete \
                        --exclude='.git' \
                        --exclude='.env.prod' \
                        ./ "$BACKEND_DIR/"
                '''
            }
        }

        stage('Sync frontend') {
            steps {
                sh '''
                    set -e

                    if [ ! -d "$FRONTEND_DIR/.git" ]; then
                        git clone -b main "$FRONTEND_REPO" "$FRONTEND_DIR"
                    else
                        git -C "$FRONTEND_DIR" fetch origin main
                        git -C "$FRONTEND_DIR" reset --hard origin/main
                        git -C "$FRONTEND_DIR" clean -fd
                    fi
                '''
            }
        }

        stage('Check env') {
            steps {
                sh '''
                    set -e
                    test -f "$BACKEND_DIR/$ENV_FILE"
                    grep -q "DJANGO_SECRET_KEY=" "$BACKEND_DIR/$ENV_FILE"
                    grep -q "POSTGRES_PASSWORD=" "$BACKEND_DIR/$ENV_FILE"
                    grep -q "MAX_BOT_SERVICE_TOKEN=" "$BACKEND_DIR/$ENV_FILE"
                    grep -q "VITE_PUBLIC_BASE_PATH=/queue/" "$BACKEND_DIR/$ENV_FILE"
                '''
            }
        }

        stage('Build images') {
            steps {
                sh '''
                    set -e
                    cd "$BACKEND_DIR"
                    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build --pull
                '''
            }
        }

        stage('Migrate and collect static') {
            steps {
                sh '''
                    set -e
                    cd "$BACKEND_DIR"

                    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d postgres redis
                    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm backend python manage.py migrate --noinput
                    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm backend python manage.py collectstatic --noinput
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    set -e
                    cd "$BACKEND_DIR"
                    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --remove-orphans
                '''
            }
        }

        stage('Smoke test') {
            steps {
                sh '''
                    set -e
                    cd "$BACKEND_DIR"

                    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

                    curl -fsS http://127.0.0.1:18081/health/
                    curl -fsS http://127.0.0.1:18080/api/schema/ > /dev/null
                '''
            }
        }
    }

    post {
        success {
            echo 'AdmissionQueue production deploy completed successfully.'
        }

        failure {
            echo 'AdmissionQueue production deploy failed. Check Jenkins logs and docker logs.'
            sh '''
                cd "$BACKEND_DIR" || exit 0
                docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps || true
                docker logs --tail=100 aq-backend-prod || true
                docker logs --tail=100 aq-rq-worker-prod || true
                docker logs --tail=100 aq-max-bot-prod || true
                docker logs --tail=100 aq-frontend-prod || true
            '''
        }
    }
}
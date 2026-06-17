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
        BACKEND_DIR = '/home/vinogradov.vs/pk-services/Queue/AdmissionQueue'
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

        stage('Pull backend') {
            steps {
                sh '''
                    set -e
                    cd "$BACKEND_DIR"
                    git fetch origin main
                    git reset --hard origin/main
                    git clean -fd
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
                '''
            }
        }

        stage('Build backend images') {
            steps {
                sh '''
                    set -e
                    cd "$BACKEND_DIR"
                    sudo docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build --pull
                '''
            }
        }

        stage('Migrate and collectstatic') {
            steps {
                sh '''
                    set -e
                    cd "$BACKEND_DIR"

                    sudo docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d postgres redis

                    sudo docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm backend python manage.py migrate --noinput

                    sudo docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm backend python manage.py collectstatic --noinput
                '''
            }
        }

        stage('Deploy backend') {
            steps {
                sh '''
                    set -e
                    cd "$BACKEND_DIR"
                    sudo docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --remove-orphans
                '''
            }
        }

        stage('Smoke test backend') {
            steps {
                sh '''
                    set -e
                    curl -fsS http://127.0.0.1:18080/api/schema/ > /dev/null
                    sudo docker ps --filter "name=aq-backend-prod"
                    sudo docker ps --filter "name=aq-rq-worker-prod"
                    sudo docker ps --filter "name=aq-max-bot-prod"
                '''
            }
        }
    }

    post {
        failure {
            sh '''
                cd "$BACKEND_DIR" || exit 0
                sudo docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps || true
                sudo docker logs --tail=100 aq-backend-prod || true
                sudo docker logs --tail=100 aq-rq-worker-prod || true
                sudo docker logs --tail=100 aq-max-bot-prod || true
            '''
        }
    }
}
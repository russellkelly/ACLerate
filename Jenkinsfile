#!/usr/bin/env groovy

/**
 * Declarative Jenkinsfile
 */
pipeline {
    agent { label 'rpm' }
    options {
        buildDiscarder(
            // Only keep the 10 most recent builds
            logRotator(numToKeepStr:'5'))
    }

    environment {
        projectName = 'ACLerate'
        emailTo = 'femi@arista.com'
        emailFrom = 'eosplus-dev+jenkins@arista.com'
    }

    stages {
        stage ('Build and Archive') {
            agent { node { label 'mockbuild' } }
            when {
                anyOf { branch 'master'; branch 'develop' }
            }
            steps {
                sh """
                    make all
                """
                archiveArtifacts artifacts: '*.swix,*.sha512sum,doc/*.pdf', fingerprint: true, onlyIfSuccessful: true
            }
        }

        stage ('Cleanup') {
            steps {
                sh 'echo Cleanup step'
            }
        }
    }

    post {
        failure {
            mail body: "${env.JOB_NAME} (${env.BUILD_NUMBER}) ${env.projectName} build error " +
                       "is here: ${env.BUILD_URL}" +
                       "Started by ${env.BUILD_CAUSE}\n" +
                       "Run status: ${env.RUN_DISPLAY_URL}\n" +
                       "Project status: ${env.JOB_DISPLAY_URL}\n" +
                       "Changes in this build: ${env.RUN_CHANGES_DISPLAY_URL}\n" +
                       "Built on node: ${env.NODE_NAME}\n",
                 from: env.emailFrom,
                 subject: "${env.projectName} ${env.JOB_NAME} (${env.BUILD_NUMBER}) build failed",
                 to: env.emailTo
        }
        success {
            mail body: "${env.JOB_NAME} (${env.BUILD_NUMBER}) ${env.projectName} build successful\n" +
                       "Started by ${env.BUILD_CAUSE}\n" +
                       "Run status: ${env.RUN_DISPLAY_URL}\n" +
                       "Project status: ${env.JOB_DISPLAY_URL}\n" +
                       "Changes in this build: ${env.RUN_CHANGES_DISPLAY_URL}\n" +
                       "Built on node: ${env.NODE_NAME}\n",
                 from: env.emailFrom,
                 subject: "${env.projectName} ${env.JOB_NAME} (${env.BUILD_NUMBER}) build successful",
                 to: env.emailTo
        }
    }
}


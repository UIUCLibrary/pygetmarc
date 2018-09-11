#!groovy
@Library("ds-utils@v0.2.0") // Uses library from https://github.com/UIUCLibrary/Jenkins_utils
import org.ds.*

def PKG_NAME = "unknown"
def PKG_VERSION = "unknown"
def DOC_ZIP_FILENAME = "doc.zip"

def reports_dir = ""

pipeline {
    agent {
        label "Windows"
    }
    options {
        disableConcurrentBuilds()  //each branch has 1 job running at a time
        timeout(20)  // Timeout after 20 minutes. This shouldn't take this long but it hangs for some reason
        checkoutToSubdirectory("source")
    }
    environment {
        build_number = VersionNumber(projectStartDate: '2018-3-27', versionNumberString: '${BUILD_DATE_FORMATTED, "yy"}${BUILD_MONTH, XX}${BUILDS_THIS_MONTH, XX}', versionPrefix: '', worstResultForIncrement: 'SUCCESS')
        PIP_CACHE_DIR="${WORKSPACE}\\pipcache\\"
    }
    triggers {
        cron('@daily')
    }
    
    parameters {
        booleanParam(name: "FRESH_WORKSPACE", defaultValue: false, description: "Purge workspace before staring and checking out source")
        string(name: "PROJECT_NAME", defaultValue: "pyGetMarc", description: "Name given to the project")
        booleanParam(name: "UNIT_TESTS", defaultValue: true, description: "Run automated unit tests")
        booleanParam(name: "TEST_RUN_DOCTEST", defaultValue: true, description: "Test documentation")
        booleanParam(name: "TEST_RUN_FLAKE8", defaultValue: true, description: "Run Flake8 static analysis")
        booleanParam(name: "TEST_RUN_MYPY", defaultValue: true, description: "Run MyPy static analysis")
        booleanParam(name: "TEST_RUN_INTEGRATION", defaultValue: true, description: "Run integration tests")
        booleanParam(name: "TEST_RUN_TOX", defaultValue: true, description: "Run Tox Tests")
        booleanParam(name: "PACKAGE", defaultValue: true, description: "Create a package")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: true, description: "Deploy to devpi on http://devpy.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to https://devpi.library.illinois.edu/production/release")
        string(name: 'URL_SUBFOLDER', defaultValue: "pygetmarc", description: 'The directory that the docs should be saved under')
    }
    stages 
    {
        stage("Configure") {
            stages{

                stage("Purge all existing data in workspace"){
                    when{
                        equals expected: true, actual: params.FRESH_WORKSPACE
                    }
                    steps{
                        deleteDir()
                        dir("source"){
                            checkout scm
                        }
                    }
                }
                stage("Cleanup"){
                    steps {
                        dir("logs"){
                            deleteDir()
                            echo "Cleaned out logs directory"
                            bat "dir"
                        }

                        dir("logs"){
                            deleteDir()
                        }

                        dir("build"){
                            deleteDir()
                            echo "Cleaned out build directory"
                            bat "dir"
                        }

                        dir("dist"){
                            deleteDir()
                            echo "Cleaned out distrubution directory"
                            bat "dir"
                        }

                        dir("${WORKSPACE}/reports"){
                            deleteDir()
                            echo "Cleaned out reports directory"
                            bat "dir"
                        }
                    }
                    post{
                        failure {
                            deleteDir()
                        }
                    }
                }
                stage("Installing required system level dependencies"){
                    steps{
                        lock("system_python_${NODE_NAME}"){
                            bat "${tool 'CPython-3.6'} -m pip install --upgrade pip --quiet"
                        }
                    }
                    post{
                        always{
                            tee("${WORKSPACE}/logs/pippackages_system_${NODE_NAME}.log") {
                                bat "${tool 'CPython-3.6'} -m pip list"
                            }
                            dir("logs"){

                                archiveArtifacts artifacts: "pippackages_system_${NODE_NAME}.log"
                            }
                        }
                    }
                }
                stage("Creating virtualenv for building"){
                    steps{
                        bat "${tool 'CPython-3.6'} -m venv venv"
                        script {
                            try {
                                bat "call venv\\Scripts\\python.exe -m pip install -U pip"
                            }
                            catch (exc) {
                                bat "${tool 'CPython-3.6'} -m venv venv"
                                bat "call venv\\Scripts\\python.exe -m pip install -U pip --no-cache-dir"
                            }
                        }
                        bat "venv\\Scripts\\pip.exe install devpi-client -r source\\requirements.txt -r source\\requirements-dev.txt --upgrade-strategy only-if-needed"
                    }
                    post{
                        success{
                            tee("${WORKSPACE}/logs/pippackages_venv_${NODE_NAME}.log") {
                                bat "venv\\Scripts\\pip.exe list"
                            }
                            dir("logs"){
                                archiveArtifacts artifacts: "pippackages_venv_${NODE_NAME}.log"
                            }
                        }
                    }
                }
                stage("Logging into DevPi"){
                    environment{
                        DEVPI_PSWD = credentials('devpi-login')
                    }
                    steps{
                        bat "venv\\Scripts\\devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}\\certs\\"
                        bat "venv\\Scripts\\devpi.exe login DS_Jenkins --password ${env.DEVPI_PSWD} --clientdir ${WORKSPACE}\\certs\\"
                    }
                }
                stage("Setting variables used by the rest of the build"){


                    steps {
                        // Set up the reports directory variable
                        script{
                            reports_dir = "${pwd tmp: true}\\reports"
                        }

                        script {
                            dir("source"){
                                PKG_NAME = bat(returnStdout: true, script: "@${tool 'CPython-3.6'}  setup.py --name").trim()
                                PKG_VERSION = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --version").trim()
                                DOC_ZIP_FILENAME = "${PKG_NAME}-${PKG_VERSION}.doc.zip"
                            }
                        }
                    }
                    post{
                        always{
                            echo """Name               = ${PKG_NAME}
Version            = ${PKG_VERSION}
documentation zip file          = ${DOC_ZIP_FILENAME}
Report Directory   = ${reports_dir}
        """
                        }
                        failure {
                            deleteDir()
                        }
                    }
                }
            }

        }

        stage('Build') {
            parallel {
                stage("Python Package"){
                    steps {
                        
                        tee('logs/build.log') {
                            dir("source"){
                                bat script: "${WORKSPACE}\\venv\\Scripts\\python.exe setup.py build -b ${WORKSPACE}\\build"
                            }
                        }
                    }
                    post{
                        always{
                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'Pep8', pattern: 'logs/build.log']]
                            archiveArtifacts artifacts: "logs/*.log"
                        }
                        failure{
                            echo "Failed to build Python package"
                        }
                        success{
                            echo "Successfully built project is ./build."
                        }
                    }
                }
                stage("Sphinx documentation"){
                    steps {
                        echo "Building docs on ${env.NODE_NAME}"
                        tee('logs/build_sphinx.log') {
                            dir("source"){
                                bat script: "${WORKSPACE}\\venv\\Scripts\\python.exe setup.py build_sphinx --build-dir ${WORKSPACE}\\build\\docs"
                            }   
                        }
                    }
                    post{
                        always {
                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'Pep8', pattern: 'logs/build_sphinx.log']]
                            archiveArtifacts artifacts: 'logs/build_sphinx.log'
                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            script{
                                // Multibranch jobs add the slash and add the branch to the job name. I need only the job name
                                def alljob = env.JOB_NAME.tokenize("/") as String[]
                                def project_name = alljob[0]
                                dir('build/docs/') {
                                    zip archive: true, dir: 'html', glob: '', zipFile: "${project_name}-${env.BRANCH_NAME}-docs-html-${env.GIT_COMMIT.substring(0,7)}.zip"
                                }
                            }
                        }
                        failure{
                            echo "Failed to build Python package"
                        }
                    }
                }
            }
        }
        stage("Testing") {
            parallel {
                stage("Run Tox test") {
                    when {
                        equals expected: true, actual: params.TEST_RUN_TOX
                    }
                    steps {
                        dir("source"){
                            script{
                                try{
                                    bat "${WORKSPACE}\\venv\\Scripts\\tox.exe --workdir ${WORKSPACE}\\.tox"
                                } catch (exc){
                                    bat "${WORKSPACE}\\venv\\Scripts\\tox.exe --workdir ${WORKSPACE}\\.tox --recreate"
                                }

                            }
                        }
                        
                    }
                    post {
                        failure {
                            archiveArtifacts artifacts: ".tox/py36/log/*.log", allowEmptyArchive: true
                            // bat "@RD /S /Q ${WORKSPACE}\\.tox"
                        }
                    }
                }
                stage("Run Doctest Tests"){
                    when {
                       equals expected: true, actual: params.TEST_RUN_DOCTEST
                    }
                    steps {
                        dir("source"){
                            bat "${WORKSPACE}\\venv\\Scripts\\sphinx-build.exe -b doctest ${WORKSPACE}\\source\\docs\\source ${WORKSPACE}\\build\\docs -d ${WORKSPACE}\\build\\docs\\doctrees"
                        }
                    }
                    post{
                        always {
                            bat "move build\\docs\\output.txt ${reports_dir}\\doctest.txt"
                            dir("${reports_dir}"){
                                bat "dir"
                                archiveArtifacts artifacts: "doctest.txt"
                            }

                        }
                    }
                }
                stage("Run MyPy Static Analysis") {
                    when {
                        equals expected: true, actual: params.TEST_RUN_MYPY
                    }
                    steps{
                        dir("reports/mypy/html"){
                            deleteDir()
                            bat "dir"
                        }
                        script{
                            tee("${pwd tmp: true}/logs/mypy.log") {
                                try{
                                    dir("source"){
                                        bat "dir"
                                        bat "${WORKSPACE}\\venv\\Scripts\\mypy.exe -p uiucprescon --html-report ${WORKSPACE}\\reports\\mypy\\html"
                                    }
                                } catch (exc) {
                                    echo "MyPy found some warnings"
                                }
                            }
                        }
                    }
                    post {
                        always {
                            dir(pwd(tmp: true)){
                                warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'MyPy', pattern: 'logs/mypy.log']], unHealthy: ''
                            }
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy/html/', reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                        }
                    }
                }
                stage("Run Integration tests") {
                    when {
                        equals expected: true, actual: params.TEST_RUN_INTEGRATION
                    }
                    steps {
                        dir("source"){
                            bat "${WORKSPACE}\\venv\\Scripts\\pip.exe install pytest-cov"
                            bat "${WORKSPACE}\\venv\\Scripts\\pytest.exe -m integration --junitxml=${WORKSPACE}/reports/junit-${env.NODE_NAME}-pytest.xml --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/coverage/  --cov-report xml:${WORKSPACE}/reports/coverage.xml --cov=uiucprescon"
                        }
                    }
                    post {
                        always{
                            publishHTML([allowMissing: true, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/coverage', reportFiles: 'index.html', reportName: 'Coverage-integration', reportTitles: ''])

                            dir("${WORKSPACE}/reports/"){
                                junit "junit-${env.NODE_NAME}-pytest.xml"
                            }

                            script {
                                try{
                                    publishCoverage
                                        autoDetectPath: 'coverage*/*.xml'
                                        adapters: [
                                            cobertura(coberturaReportFile:"reports/coverage.xml")
                                        ]
                                } catch(exc){
                                    echo "cobertura With Coverage API failed. Falling back to cobertura plugin"
                                    cobertura autoUpdateHealth: false, autoUpdateStability: false, coberturaReportFile: "reports/coverage.xml", conditionalCoverageTargets: '70, 0, 0', failUnhealthy: false, failUnstable: false, lineCoverageTargets: '80, 0, 0', maxNumberOfBuilds: 0, methodCoverageTargets: '80, 0, 0', onlyStable: false, sourceEncoding: 'ASCII', zoomCoverageChart: false
                                }
                            }
                            bat "del reports\\coverage.xml"
                        }
                        failure{
                            dir("${WORKSPACE}/reports"){
                                bat "tree /A /F"
                            }
                        }
                    }
                }

            }
        }
    
        stage("Packaging") {
            steps {
                dir("source"){
                    bat "${WORKSPACE}\\venv\\Scripts\\python.exe setup.py bdist_wheel sdist -d ${WORKSPACE}\\dist bdist_wheel -d ${WORKSPACE}\\dist"
                }

                dir("dist") {
                    archiveArtifacts artifacts: "*.whl", fingerprint: true
                    archiveArtifacts artifacts: "*.tar.gz", fingerprint: true
                    archiveArtifacts artifacts: "*.zip", fingerprint: true
                }
            }
        }

        stage("Deploying to Devpi") {
            when {
                allOf{
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
            }
            steps {
                bat "venv\\Scripts\\devpi.exe use https://devpi.library.illinois.edu"
                withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                    bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"

                }
                bat "venv\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
                script {
                        bat "venv\\Scripts\\devpi.exe upload --from-dir dist"
                        try {
                            bat "venv\\Scripts\\devpi.exe upload --only-docs --from-dir ${WORKSPACE}\\dist\\${DOC_ZIP_FILENAME}"
                        } catch (exc) {
                            echo "Unable to upload to devpi with docs."
                        }
                    }

            }
        }
        stage("Test DevPi packages") {
            when {
                allOf{
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
            }


            parallel {
                stage("Source Distribution: .tar.gz") {
                    agent {
                        node {
                            label "Windows && Python3"
                        }
                    }
                    options {
                        skipDefaultCheckout(true)
                    }
                    stages{
                        stage("Building DevPi Testing venv for .tar.gz package"){
                            steps{
                                bat "${tool 'CPython-3.6'} -m venv venv"
                                bat "venv\\Scripts\\python.exe -m pip install --upgrade pip"
                                bat "venv\\Scripts\\pip.exe install tox devpi-client"
                                withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                                    bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"

                                }
                                bat "venv\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
                            }
                        }
                        stage("DevPi Testing tar.gz package"){
                            steps {
                                bat script: "venv\\Scripts\\devpi.exe test --index https://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging ${PKG_NAME} -s tar.gz  --verbose"
                            }
                        }
                    }

                    post {
                        failure {
                            echo "Tests for .tar.gz source on DevPi failed."
                        }
                    }

                }
                stage("Source Distribution: .zip") {
                    agent {
                        node {
                            label "Windows && Python3"
                        }
                    }
                    options {
                        skipDefaultCheckout(true)
                    }
                    stages{
                        stage("Building DevPi Testing venv for .zip package"){
                            steps{
                                bat "${tool 'CPython-3.6'} -m venv venv"
                                bat "venv\\Scripts\\python.exe -m pip install --upgrade pip"
                                bat "venv\\Scripts\\pip.exe install tox devpi-client"
                                withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                                    bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"

                                }
                                bat "venv\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
                            }
                        }
                        stage("DevPi Testing .zip package"){
                            steps {
                                bat script: "venv\\Scripts\\devpi.exe test --index https://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging ${PKG_NAME} -s zip --verbose"
                            }
                        }
                    }
                }
                stage("Built Distribution: .whl") {
                    agent {
                        node {
                            label "Windows && Python3"
                        }
                    }
                    options {
                        skipDefaultCheckout(true)
                    }
                    stages{
                        stage("Building DevPi Testing venv for .whl package"){
                            steps{
                                bat "${tool 'CPython-3.6'} -m venv venv"
                                bat "venv\\Scripts\\python.exe -m pip install --upgrade pip"
                                bat "venv\\Scripts\\pip.exe install tox devpi-client"
                                withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                                    bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"

                                }
                                bat "venv\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
                            }
                        }
                        stage("DevPi Testing .whl package"){
                            steps {
                                bat script: "venv\\Scripts\\devpi.exe test --index https://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging ${PKG_NAME} -s whl  --verbose"
                            }
                        }
                    }
                }
            }
            post {
                success {
                    echo "it Worked. Pushing file to ${env.BRANCH_NAME} index"
                    script {
                        withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                            bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                            bat "venv\\Scripts\\devpi.exe use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                            bat "venv\\Scripts\\devpi.exe push ${PKG_NAME}==${PKG_VERSION} ${DEVPI_USERNAME}/${env.BRANCH_NAME}"
                        }

                    }
                }
                failure {
                    echo "At least one package format on DevPi failed."
                }
            }
        }
        stage("Deploy"){
            parallel {
                stage("Deploy Online Documentation") {
                    when{
                        equals expected: true, actual: params.DEPLOY_DOCS
                    }
                    steps{
                        script {
                            if(!params.BUILD_DOCS){
                                bat "pipenv run python setup.py build_sphinx"
                            }
                        }
                        
                        dir("build/docs/html/"){
                            input 'Update project documentation?'
                            sshPublisher(
                                publishers: [
                                    sshPublisherDesc(
                                        configName: 'apache-ns - lib-dccuser-updater', 
                                        sshLabel: [label: 'Linux'], 
                                        transfers: [sshTransfer(excludes: '', 
                                        execCommand: '', 
                                        execTimeout: 120000, 
                                        flatten: false, 
                                        makeEmptyDirs: false, 
                                        noDefaultExcludes: false, 
                                        patternSeparator: '[, ]+', 
                                        remoteDirectory: "${params.DEPLOY_DOCS_URL_SUBFOLDER}", 
                                        remoteDirectorySDF: false, 
                                        removePrefix: '', 
                                        sourceFiles: '**')], 
                                    usePromotionTimestamp: false, 
                                    useWorkspaceInPromotion: false, 
                                    verbose: true
                                    )
                                ]
                            )
                        }
                    }
                }
                stage("Deploy to DevPi Production") {
                    when {
                        allOf{
                            equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                            equals expected: true, actual: params.DEPLOY_DEVPI
                            branch "master"
                        }
                    }
                    steps {
                        script {
                            input "Release ${PKG_NAME} ${PKG_VERSION} to DevPi Production?"
                            withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                                bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"         
                            }

                            bat "venv\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
                            bat "venv\\Scripts\\devpi.exe push ${PKG_NAME}==${PKG_VERSION} production/release"
                        }
                    }
                }
            }
        }
    }
    post {
        cleanup{
            echo "Cleaning up."
            script {
                if(fileExists('source/setup.py')){
                    dir("source"){
                        try{
                            bat "${WORKSPACE}\\venv\\Scripts\\python.exe setup.py clean --all"
                        } catch (Exception ex) {
                            echo "Unable to succesfully run clean. Purging source directory."
                            deleteDir()
                        }   
                    }
                }                
                if (env.BRANCH_NAME == "master" || env.BRANCH_NAME == "dev"){
                    withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                        bat "venv\\Scripts\\devpi.exe login DS_Jenkins --password ${DEVPI_PASSWORD}"
                        bat "venv\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
                    }

                    def devpi_remove_return_code = bat returnStatus: true, script:"venv\\Scripts\\devpi.exe remove -y ${PKG_NAME}==${PKG_VERSION}"
                    echo "Devpi remove exited with code ${devpi_remove_return_code}."
                }
            }
            bat "dir"
        } 
    }
}

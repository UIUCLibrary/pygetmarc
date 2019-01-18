#!groovy
//@Library("ds-utils@v0.2.0") // Uses library from https://github.com/UIUCLibrary/Jenkins_utils
//import org.ds.*
@Library(["devpi", "PythonHelpers"]) _

//def PKG_NAME = "unknown"
//def PKG_VERSION = "unknown"
//def DOC_ZIP_FILENAME = "doc.zip"

//def reports_dir = ""

def remove_from_devpi(devpiExecutable, pkgName, pkgVersion, devpiIndex, devpiUsername, devpiPassword){
    script {
                try {
                    bat "${devpiExecutable} login ${devpiUsername} --password ${devpiPassword}"
                    bat "${devpiExecutable} use ${devpiIndex}"
                    bat "${devpiExecutable} remove -y ${pkgName}==${pkgVersion}"
                } catch (Exception ex) {
                    echo "Failed to remove ${pkgName}==${pkgVersion} from ${devpiIndex}"
            }

    }
}

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
        PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
        PKG_NAME = pythonPackageName(toolName: "CPython-3.6")
        PKG_VERSION = pythonPackageVersion(toolName: "CPython-3.6")
        DOC_ZIP_FILENAME = "${env.PKG_NAME}-${env.PKG_VERSION}.doc.zip"
        DEVPI = credentials("DS_devpi")
        build_number = VersionNumber(projectStartDate: '2018-3-27', versionNumberString: '${BUILD_DATE_FORMATTED, "yy"}${BUILD_MONTH, XX}${BUILDS_THIS_MONTH, XX}', versionPrefix: '', worstResultForIncrement: 'SUCCESS')
        PIP_CACHE_DIR="${WORKSPACE}\\pipcache\\"
    }
    triggers {
        cron('@daily')
    }
    
    parameters {
        booleanParam(name: "FRESH_WORKSPACE", defaultValue: false, description: "Purge workspace before staring and checking out source")
        string(name: "PROJECT_NAME", defaultValue: "pyGetMarc", description: "Name given to the project")
        booleanParam(name: "TEST_RUN_DOCTEST", defaultValue: true, description: "Test documentation")
        booleanParam(name: "TEST_RUN_FLAKE8", defaultValue: true, description: "Run Flake8 static analysis")
        booleanParam(name: "TEST_RUN_MYPY", defaultValue: true, description: "Run MyPy static analysis")
        booleanParam(name: "TEST_RUN_INTEGRATION", defaultValue: true, description: "Run integration tests")
        booleanParam(name: "TEST_RUN_UNIT_TESTS", defaultValue: true, description: "Run automated unit tests")
        booleanParam(name: "TEST_RUN_TOX", defaultValue: true, description: "Run Tox Tests")
        booleanParam(name: "PACKAGE", defaultValue: true, description: "Create a package")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpy.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to https://devpi.library.illinois.edu/production/release")
        string(name: 'URL_SUBFOLDER', defaultValue: "pygetmarc", description: 'The directory that the docs should be saved under')
    }
    stages 
    {
        stage("Configure") {
            environment {
                PATH = "${tool 'CPython-3.6'};$PATH"
            }
            stages{

                stage("Purge all existing data in workspace"){

                    when{
                        anyOf{
                                equals expected: true, actual: params.FRESH_WORKSPACE
                                triggeredBy "TimerTriggerCause"
                            }
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
                            bat "dir > nul"
                        }

                        dir("logs"){
                            deleteDir()
                            bat "dir > nul"
                        }

                        dir("build"){
                            deleteDir()
                            echo "Cleaned out build directory"
                            bat "dir > nul"
                        }

                        dir("dist"){
                            deleteDir()
                            echo "Cleaned out distribution directory"
                            bat "dir > nul"
                        }

                        dir("${WORKSPACE}/reports"){
                            deleteDir()
                            echo "Cleaned out reports directory"
                            bat "dir > nul"
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
                            bat "python -m pip install --upgrade pip"
                        }
                    }
                    post{
                        always{
                            lock("system_python_${NODE_NAME}"){
                                bat "python -m pip list > logs\\pippackages_system_${NODE_NAME}.log"
                            }
                            archiveArtifacts artifacts: "logs/pippackages_system_${NODE_NAME}.log"
                        }
                    }
                }
                stage("Creating virtualenv for building"){
                    steps{
                        bat "python -m venv venv"
                        script {
                            try {
                                bat "call venv\\Scripts\\python.exe -m pip install -U pip"
                            }
                            catch (exc) {
                                bat "${tool 'CPython-3.6'}\\python -m venv venv"
                                bat "call venv\\Scripts\\python.exe -m pip install -U pip --no-cache-dir"
                            }
                        }
                        bat "venv\\Scripts\\pip.exe install devpi-client pytest pytest-cov lxml -r source\\requirements.txt -r source\\requirements-dev.txt --upgrade-strategy only-if-needed"
                    }
                    post{
                        success{                            
                            bat "venv\\Scripts\\pip.exe list > ${WORKSPACE}\\logs\\pippackages_venv_${NODE_NAME}.log"
                            archiveArtifacts artifacts: "logs/pippackages_venv_${NODE_NAME}.log"                            
                        }
                    }
                }
            }
            post{
                always{
                    echo "Configured ${env.PKG_NAME}, version ${env.PKG_VERSION}, for testing."
                }

            }

        }

        stage('Build') {
            parallel {
                stage("Python Package"){
                    steps {
                        
                        
                        dir("source"){
                            powershell "& ${WORKSPACE}\\venv\\Scripts\\python.exe setup.py build -b ${WORKSPACE}\\build  | tee ${WORKSPACE}\\logs\\build.log"
                        }
                        
                    }
                    post{
                        always{
                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'Pep8', pattern: 'logs/build.log']]
                            archiveArtifacts artifacts: "logs/build.log"
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
                        // tee('logs/build_sphinx.log') {
                        dir("source"){
                            powershell "& ${WORKSPACE}\\venv\\Scripts\\python.exe setup.py build_sphinx --build-dir ${WORKSPACE}\\build\\docs | tee ${WORKSPACE}\\logs\\build_sphinx.log"
                        }   
                    // }
                    }
                    post{
                        always {
                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'Pep8', pattern: 'logs/build_sphinx.log']]
                            archiveArtifacts artifacts: 'logs/build_sphinx.log'
                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            zip archive: true, dir: "build/docs/html", glob: '', zipFile: "dist/${env.DOC_ZIP_FILENAME}"
                            stash includes: 'build/docs/html/**', name: 'docs'
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
                            bat "move build\\docs\\output.txt reports\\doctest.txt"
                            archiveArtifacts artifacts: "reports/doctest.txt"

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
                            try{
                                dir("source"){
                                    bat "dir"
                                    bat "${WORKSPACE}\\venv\\Scripts\\mypy.exe -p uiucprescon --html-report ${WORKSPACE}\\reports\\mypy\\html > ${WORKSPACE}\\logs\\mypy.log"
                                }
                            } catch (exc) {
                                echo "MyPy found some warnings"
                            }
                        }
                    }
                    post {
                        always {
                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'MyPy', pattern: 'logs/mypy.log']], unHealthy: ''
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
                            lock("${WORKSPACE}/reports/coverage.xml"){
                                bat "${WORKSPACE}\\venv\\Scripts\\pytest.exe -m integration --junitxml=${WORKSPACE}/reports/junit-${env.NODE_NAME}-pytest.xml --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/coverage/  --cov-report xml:${WORKSPACE}/reports/coverage.xml --cov=uiucprescon --cov-append"
                            }
                        }
                    }
                    post {
                        always{
                            publishHTML([allowMissing: true, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/coverage', reportFiles: 'index.html', reportName: 'Coverage-integration', reportTitles: ''])
                            junit "reports/junit-${env.NODE_NAME}-pytest.xml"
                        }
                    }
                }
                stage("Run Unit tests") {
                    when {
                        equals expected: true, actual: params.TEST_RUN_UNIT_TESTS
                    }
                    steps {
                        dir("source"){
                            bat "${WORKSPACE}\\venv\\Scripts\\pip.exe install pytest-cov"
                            lock("${WORKSPACE}/reports/coverage.xml"){
                                bat "${WORKSPACE}\\venv\\Scripts\\pytest.exe --junitxml=${WORKSPACE}/reports/junit-${env.NODE_NAME}-pytest.xml --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/coverage/  --cov-report xml:${WORKSPACE}/reports/coverage.xml --cov=uiucprescon --cov-append"
                            }
                        }
                    }
                    post {
                        always{
                            publishHTML([allowMissing: true, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/coverage', reportFiles: 'index.html', reportName: 'Coverage-Unit tests', reportTitles: ''])
                                junit "reports/junit-${env.NODE_NAME}-pytest.xml"
                        }
                    }
                }
            }
            post{
                always{
                    script {
                        try{
                            publishCoverage
                                autoDetectPath: 'coverage*/*.xml'
                                adapters: [
                                    cobertura(coberturaReportFile:"reports/coverage.xml")
                                ]
                        } catch(exc){
                            echo "cobertura With Coverage API failed. Falling back to cobertura plugin"
                            cobertura(
                                autoUpdateHealth: false,
                                autoUpdateStability: false,
                                coberturaReportFile: "reports/coverage.xml",
                                conditionalCoverageTargets: '70, 0, 0',
                                failUnhealthy: false,
                                failUnstable: false,
                                lineCoverageTargets: '80, 0, 0',
                                maxNumberOfBuilds: 0,
                                methodCoverageTargets: '80, 0, 0',
                                onlyStable: false,
                                sourceEncoding: 'ASCII',
                                zoomCoverageChart: false
                            )
                        }
                    }
                }
                cleanup{
                    bat "del reports\\coverage.xml"
                }
            }
        }
    
        stage("Packaging") {
            steps {
                dir("source"){
                    bat "${WORKSPACE}\\venv\\Scripts\\python.exe setup.py bdist_wheel sdist -d ${WORKSPACE}\\dist --format zip bdist_wheel -d ${WORKSPACE}\\dist"
                }
            }
            post{
                success{
                    archiveArtifacts artifacts: "dist/*.whl,dist/*.tar.gz,dist/*.zip", fingerprint: true
                    stash includes: 'dist/*.*', name: "dist"
                }
            }
        }

        stage("Deploying to DevPi") {
           when {
                allOf{
                    anyOf{
                        equals expected: true, actual: params.DEPLOY_DEVPI
                        triggeredBy "TimerTriggerCause"
                    }
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
            }
            stages{
                stage("Upload to Devpi staging") {
                    steps {
                        bat "venv\\Scripts\\devpi.exe use https://devpi.library.illinois.edu"
                        withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                            bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"

                        }
                        bat "venv\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
                        script {
                                bat "venv\\Scripts\\devpi.exe upload --from-dir dist"
                                try {
                                    bat "venv\\Scripts\\devpi.exe upload --only-docs --from-dir ${WORKSPACE}\\dist\\${env.DOC_ZIP_FILENAME}"
                                } catch (exc) {
                                    echo "Unable to upload to devpi with docs."
                                }
                            }

                    }
                }
                stage("Test DevPi packages") {
                    parallel {
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
                                stage("Building DevPi Testing venv for .tar.gz package"){
                                    steps{
                                        bat "${tool 'CPython-3.6'}\\python -m venv venv"
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
                                        devpiTest(
                                            devpiExecutable: "venv\\Scripts\\devpi.exe",
                                            url: "https://devpi.library.illinois.edu",
                                            index: "${env.BRANCH_NAME}_staging",
                                            pkgName: "${env.PKG_NAME}",
                                            pkgVersion: "${env.PKG_VERSION}",
                                            pkgRegex: "zip"
                                        )
                                    }
                                }
                            }

                            post {
                                cleanup{
                                        cleanWs deleteDirs: true, patterns: [
                                            [pattern: 'certs', type: 'INCLUDE']
                                        ]
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
                                        bat "${tool 'CPython-3.6'}\\python -m venv venv"
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
                                        devpiTest(
                                            devpiExecutable: "venv\\Scripts\\devpi.exe",
                                            url: "https://devpi.library.illinois.edu",
                                            index: "${env.BRANCH_NAME}_staging",
                                            pkgName: "${env.PKG_NAME}",
                                            pkgVersion: "${env.PKG_VERSION}",
                                            pkgRegex: "whl"
                                        )
                                    }

                                }
                            }
                            post{
                                cleanup{
                                    cleanWs deleteDirs: true, patterns: [
                                        [pattern: 'certs', type: 'INCLUDE']
                                    ]
                                }
                            }
                        }
                    }
                }
                stage("Deploy to DevPi Production") {
                    when {
                        allOf{
                            equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                            branch "master"
                        }
                    }
                    steps {
                        script {
                            input "Release ${env.PKG_NAME} ${env.PKG_VERSION} to DevPi Production?"
                            withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                                bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                            }

                            bat "venv\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
                            bat "venv\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} production/release"
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
                            bat "venv\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} ${DEVPI_USERNAME}/${env.BRANCH_NAME}"
                        }

                    }

                }
                failure {
                    echo "At least one package format on DevPi failed."
                }
                cleanup{
                    remove_from_devpi("venv\\Scripts\\devpi.exe", "${env.PKG_NAME}", "${env.PKG_VERSION}", "/${env.DEVPI_USR}/${env.BRANCH_NAME}_staging", "${env.DEVPI_USR}", "${env.DEVPI_PSW}")
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

            }
            cleanWs deleteDirs: true, patterns: [
                    [pattern: 'build*', type: 'INCLUDE'],
                    [pattern: 'certs', type: 'INCLUDE'],
                    [pattern: 'dist*', type: 'INCLUDE'],
                    [pattern: 'logs*', type: 'INCLUDE'],
                    [pattern: 'reports*', type: 'INCLUDE'],
                    [pattern: '.tox', type: 'INCLUDE'],
                    [pattern: '*@tmp', type: 'INCLUDE']
                    ]
        }
    }
}

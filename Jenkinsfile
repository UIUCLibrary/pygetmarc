#!groovy
@Library(["devpi", "PythonHelpers"]) _



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
        label "Windows && Python3"
    }
    options {
        disableConcurrentBuilds()  //each branch has 1 job running at a time
        timeout(20)  // Timeout after 20 minutes. This shouldn't take this long but it hangs for some reason
        checkoutToSubdirectory("source")
    }
    environment {
        PYTHON_LOCATION = "${tool 'CPython-3.6'}"
//        PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
        PKG_NAME = pythonPackageName(toolName: "CPython-3.6")
        PKG_VERSION = pythonPackageVersion(toolName: "CPython-3.6")

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
        booleanParam(name: "TEST_RUN_INTEGRATION", defaultValue: true, description: "Run integration tests")
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
            environment{
                PATH = "${env.PYTHON_LOCATION};${PATH}"
            }
            stages{

                stage("Purge All Existing Data in Workspace"){

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
                stage("Getting Distribution Info"){
                    environment{
                        PATH = "${tool 'CPython-3.7'};$PATH"
                    }
                    steps{
                        dir("source"){
                            bat "python setup.py dist_info"
                        }
                    }
                    post{
                        success{
                            dir("source"){
                                stash includes: "uiucprescon_getmarc.dist-info/**", name: 'DIST-INFO'
                                archiveArtifacts artifacts: "uiucprescon_getmarc.dist-info/**"
                            }
                        }
                    }
                }
                stage("Creating Virtualenv for Building"){
                    environment{
                        PATH = "${tool 'CPython-3.6'};$PATH"
                    }
                    steps{
                        bat "python -m venv venv\\36"
                        script {
                            try {
                                bat "call venv\\36\\Scripts\\python.exe -m pip install -U pip"
                            }
                            catch (exc) {
                                bat "python -m venv venv\\36"
                                bat "venv\\36\\Scripts\\python.exe -m pip install -U pip --no-cache-dir"
                            }
                        }
                        bat 'venv\\36\\Scripts\\pip.exe install -r source\\requirements.txt --upgrade-strategy only-if-needed && venv\\36\\Scripts\\pip.exe install \"tox>=3.7,<3.8\" '
                    }
                    post{
                        success{
                            bat "(if not exist logs mkdir logs) && venv\\36\\Scripts\\pip.exe list > ${WORKSPACE}\\logs\\pippackages_venv_${NODE_NAME}.log"
                            archiveArtifacts artifacts: "logs/pippackages_venv_${NODE_NAME}.log"                            
                        }
                    }
                }
            }
            post{
                success{
                    echo "Configured ${env.PKG_NAME}, version ${env.PKG_VERSION}, for testing."
                }

            }

        }

        stage('Build') {
            environment{
                PATH = "${WORKSPACE}\\venv\\36\\Scripts;${PATH}"
            }
            parallel {
                stage("Python Package"){
                    steps {
                        
                        
                        dir("source"){
                            powershell "& python.exe setup.py build -b ${WORKSPACE}\\build  | tee ${WORKSPACE}\\logs\\build.log"
                        }
                        
                    }
                    post{
                        always{
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
                stage("Sphinx Documentation"){
                    environment{
                        DOC_ZIP_FILENAME = "${env.PKG_NAME}-${env.PKG_VERSION}.doc.zip"
                    }
                    steps {
                        bat "pip install sphinx"
                        echo "Building docs on ${env.NODE_NAME}"
                        dir("source"){
                            bat "sphinx-build.exe -b html ${WORKSPACE}\\source\\docs\\source ${WORKSPACE}\\build\\docs\\html -d ${WORKSPACE}\\build\\docs\\doctrees -w ${WORKSPACE}\\logs\\build_sphinx.log"
                        }
                    }
                    post{
                        always {
                            recordIssues(tools: [sphinxBuild(name: 'Sphinx Documentation Build', pattern: 'logs/build_sphinx.log')])
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
            stages{
                stage("Installing Testing Python Packages"){
                    steps{
                        bat "venv\\36\\Scripts\\pip.exe install pytest pytest-cov lxml -r source\\requirements-dev.txt --upgrade-strategy only-if-needed"
                    }
                }
                stage("Running Tests"){
                    environment {
                        PATH = "${WORKSPACE}\\venv\\36\\Scripts;${PATH}"
                    }
                    parallel {
                        stage("Run Tox Test") {
                            when {
                                equals expected: true, actual: params.TEST_RUN_TOX
                            }
                            environment {
                                PATH = "${WORKSPACE}\\venv\\36\\Scripts;${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
                            }
                            steps {
                                dir("source"){
                                    script{
                                        try{
                                            bat (
                                                label: "Run Tox",
                                                script: "tox --parallel=auto --parallel-live --workdir ${WORKSPACE}\\.tox -v --result-json=${WORKSPACE}\\logs\\tox_report.json"
                                            )
                                        } catch (exc) {
                                            bat (
                                                label: "Run Tox with new environments",
                                                script: "tox --recreate --parallel=auto --parallel-live --workdir ${WORKSPACE}\\.tox -v --result-json=${WORKSPACE}\\logs\\tox_report.json"
                                            )
                                        }
//                                        try{
//                                          bat "tox.exe --parallel=auto --parallel-live --workdir ${WORKSPACE}\\.tox"
//                                        } catch (exc) {
//                                          bat "tox.exe --parallel=auto --parallel-live --workdir ${WORKSPACE}\\.tox -vv --recreate"
//                                        }
                                    }
                                }

                            }
                            post {
                                always {
                                    archiveArtifacts allowEmptyArchive: true, artifacts: '.tox/py*/log/*.log,.tox/log/*.log,logs/tox_report.json'
                                    recordIssues(tools: [pep8(id: 'tox', name: 'Tox', pattern: '.tox/py*/log/*.log,.tox/log/*.log')])
                                }
                                cleanup{
                                    cleanWs(
                                        patterns: [
                                            [pattern: '.tox/py*/log/*.log', type: 'INCLUDE'],
                                            [pattern: '.tox/log/*.log', type: 'INCLUDE'],
                                            [pattern: 'logs/rox_report.json', type: 'INCLUDE']
                                        ]
                                    )
                                }
                            }
                        }
                        stage("Run Doctest Tests"){
                            steps {
                                dir("source"){
                                    bat "sphinx-build.exe -b doctest docs\\source ${WORKSPACE}\\build\\docs -d ${WORKSPACE}\\build\\docs\\doctrees -w ${WORKSPACE}\\logs\\doctest.log"
                                }
                            }
                            post{
                                always {
                                    archiveArtifacts artifacts: "logs/doctest.log"

                                }
                            }
                        }
                        stage("Run MyPy Static Analysis") {
                            steps{
                                bat "(if not exist reports\\mypy\\html mkdir reports\\mypy\\html) && (if not exist logs mkdir logs)"
                                script{
                                    try{
                                        dir("source"){
                                            bat "mypy.exe -p uiucprescon --html-report ${WORKSPACE}\\reports\\mypy\\html > ${WORKSPACE}\\logs\\mypy.log"
                                        }
                                    } catch (exc) {
                                        echo "MyPy found some warnings"
                                    }
                                }
                            }
                            post {
                                always {
                                    recordIssues(tools: [myPy(pattern: 'logs/mypy.log')])
                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy/html/', reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                                }
                            }
                        }
                        stage("Run Integration Tests") {
                            when {
                                equals expected: true, actual: params.TEST_RUN_INTEGRATION
                            }
                            steps {
                                dir("source"){

                                    lock("${WORKSPACE}/reports/coverage.xml"){
                                        bat "pytest.exe -m integration --junitxml=${WORKSPACE}/reports/junit-${env.NODE_NAME}-pytest.xml --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/coverage/  --cov-report xml:${WORKSPACE}/reports/coverage.xml --cov=uiucprescon --cov-append"
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
                        stage("Run Unit Tests") {
                            steps {
                                dir("source"){
                                    lock("${WORKSPACE}/reports/coverage.xml"){
                                        bat "pytest.exe --junitxml=${WORKSPACE}/reports/junit-${env.NODE_NAME}-pytest.xml --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/coverage/  --cov-report xml:${WORKSPACE}/reports/coverage.xml --cov=uiucprescon --cov-append"
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
                }
            }
            post{
                success{
                    publishCoverage(
                        adapters: [
                            coberturaAdapter('reports/coverage.xml')
                            ],
                        sourceFileResolver: sourceFiles('STORE_ALL_BUILD'),
                        tag: 'coverage'
                    )
                }
                cleanup{
                    bat "del reports\\coverage.xml"
                }
            }
        }
    
        stage("Packaging") {
            steps {
                dir("source"){
                    bat "${WORKSPACE}\\venv\\36\\Scripts\\python.exe setup.py bdist_wheel sdist -d ${WORKSPACE}\\dist --format zip bdist_wheel -d ${WORKSPACE}\\dist"
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
            options{
                timestamps()
            }
            environment{
                PATH = "${WORKSPACE}\\venv\\36\\Scripts;${tool 'CPython-3.6'};${PATH}"
            }
            stages{
                stage("Upload to DevPi Staging") {
                    steps {
                        bat "pip.exe install devpi-client"
                        bat "devpi.exe use https://devpi.library.illinois.edu"
                        bat "devpi use https://devpi.library.illinois.edu && devpi login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} && devpi use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging && devpi upload --from-dir dist"
                    }
                }
                stage("Test DevPi Packages") {
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
                                stage("Building DevPi Testing venv for .zip Package"){
                                    environment {
                                        PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
                                    }
                                    steps{
                                        lock("system_python_${NODE_NAME}"){
                                            bat "python -m venv venv"
                                        }
                                        bat "venv\\Scripts\\python.exe -m pip install pip --upgrade && venv\\Scripts\\pip.exe install setuptools --upgrade && venv\\Scripts\\pip.exe install \"tox<3.7\" detox devpi-client"
                                    }
                                }
                                stage("Testing DevPi zip Package"){
                                    options{
                                        timeout(20)
                                    }
                                    environment {
                                        PATH = "${WORKSPACE}\\venv\\Scripts;${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
                                    }
                                    steps {
                                        echo "Testing Source tar.gz package in devpi"

                                        devpiTest(
                                            devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                                            url: "https://devpi.library.illinois.edu",
                                            index: "${env.BRANCH_NAME}_staging",
                                            pkgName: "${env.PKG_NAME}",
                                            pkgVersion: "${env.PKG_VERSION}",
                                            pkgRegex: "zip",
                                            detox: false
                                        )
                                        echo "Finished testing Source Distribution: .zip"
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
                            environment {
                                PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.6'}\\Scripts;${tool 'CPython-3.7'};$PATH"
                            }
                            options {
                                skipDefaultCheckout(true)
                            }
                            stages{
                                stage("Creating venv to Test Whl"){
                                    steps {
                                        lock("system_python_${NODE_NAME}"){
                                            bat "if not exist venv\\36 mkdir venv\\36"
                                            bat "\"${tool 'CPython-3.6'}\\python.exe\" -m venv venv\\36"
                                            bat "if not exist venv\\37 mkdir venv\\37"
                                            bat "\"${tool 'CPython-3.7'}\\python.exe\" -m venv venv\\37"
                                        }
                                        bat "venv\\36\\Scripts\\python.exe -m pip install pip --upgrade && venv\\36\\Scripts\\pip.exe install setuptools --upgrade && venv\\36\\Scripts\\pip.exe install \"tox<3.7\" devpi-client"
                                    }

                                }
                                stage("Testing DevPi .whl Package"){
                                    options{
                                        timeout(20)
                                    }
                                    environment{
                                       PATH = "${WORKSPACE}\\venv\\36\\Scripts;${tool 'CPython-3.6'};${tool 'CPython-3.6'}\\Scripts;${tool 'CPython-3.7'};$PATH"
                                    }
                                    steps {
                                        echo "Testing Whl package in devpi"
                                        devpiTest(
//                                                devpiExecutable: "venv\\36\\Scripts\\devpi.exe",
                                            devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                                            url: "https://devpi.library.illinois.edu",
                                            index: "${env.BRANCH_NAME}_staging",
                                            pkgName: "${env.PKG_NAME}",
                                            pkgVersion: "${env.PKG_VERSION}",
                                            pkgRegex: "whl",
                                            detox: false
                                            )

                                        echo "Finished testing Built Distribution: .whl"
                                    }
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
                                bat "venv\\36\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                            }

                            bat "venv\\36\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
                            bat "venv\\36\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} production/release"
                        }
                    }
                }
            }
            post {
                success {
                    echo "it Worked. Pushing file to ${env.BRANCH_NAME} index"
                    script {
                        withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                            bat "venv\\36\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                            bat "venv\\36\\Scripts\\devpi.exe use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                            bat "venv\\36\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} ${DEVPI_USERNAME}/${env.BRANCH_NAME}"
                        }

                    }

                }
                failure {
                    echo "At least one package format on DevPi failed."
                }
                cleanup{
                    remove_from_devpi("venv\\Scripts\\36\\devpi.exe", "${env.PKG_NAME}", "${env.PKG_VERSION}", "/${env.DEVPI_USR}/${env.BRANCH_NAME}_staging", "${env.DEVPI_USR}", "${env.DEVPI_PSW}")
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
//            echo "Cleaning up."
//            script {
//                if(fileExists('source/setup.py')){
//                    dir("source"){
//                        try{
//                            bat "${WORKSPACE}\\venv\\Scripts\\python.exe setup.py clean --all"
//                        } catch (Exception ex) {
//                            echo "Unable to succesfully run clean. Purging source directory."
//                            deleteDir()
//                        }
//                    }
//                }
//
//            }
            cleanWs deleteDirs: true, patterns: [
                    [pattern: 'source', type: 'INCLUDE'],
                    [pattern: 'build*', type: 'INCLUDE'],
                    [pattern: 'certs', type: 'INCLUDE'],
                    [pattern: 'dist*', type: 'INCLUDE'],
                    [pattern: 'logs*', type: 'INCLUDE'],
                    [pattern: 'reports*', type: 'INCLUDE'],
//                    [pattern: '.tox', type: 'INCLUDE'],
                    [pattern: '*@tmp', type: 'INCLUDE']
                    ]
        }
    }
}

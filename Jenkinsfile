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
    agent none
    options {
        disableConcurrentBuilds()  //each branch has 1 job running at a time
        timeout(20)  // Timeout after 20 minutes. This shouldn't take this long but it hangs for some reason
    }
    environment {
//        PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
        build_number = VersionNumber(projectStartDate: '2018-3-27', versionNumberString: '${BUILD_DATE_FORMATTED, "yy"}${BUILD_MONTH, XX}${BUILDS_THIS_MONTH, XX}', versionPrefix: '', worstResultForIncrement: 'SUCCESS')
//        PIP_CACHE_DIR="${WORKSPACE}\\pipcache\\"
    }
    triggers {
        cron('@daily')
    }
    
    parameters {
        booleanParam(name: "FRESH_WORKSPACE", defaultValue: false, description: "Purge workspace before staring and checking out source")
        string(name: "PROJECT_NAME", defaultValue: "pyGetMarc", description: "Name given to the project")
        booleanParam(name: "TEST_RUN_INTEGRATION", defaultValue: true, description: "Run integration tests")
        booleanParam(name: "TEST_RUN_TOX", defaultValue: true, description: "Run Tox Tests")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpy.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to https://devpi.library.illinois.edu/production/release")
        string(name: 'URL_SUBFOLDER', defaultValue: "pygetmarc", description: 'The directory that the docs should be saved under')
    }
    stages {
        stage("Getting Distribution Info"){
            agent {
              dockerfile {
                    filename 'ci\\docker\\windows\\Dockerfile'
                    label 'windows&&docker'
                  }
            }
            steps{
                bat "python setup.py dist_info"
            }
            post{
                success{
                    stash includes: "uiucprescon_getmarc.dist-info/**", name: 'DIST-INFO'
                    archiveArtifacts artifacts: "uiucprescon_getmarc.dist-info/**"
                }
                cleanup{
                    cleanWs notFailBuild: true
                }
            }
        }

        //tage('Build') {
        //   parallel {

                //stage("Python Package"){
                //    agent {
                //      dockerfile {
                //            filename 'ci\\docker\\windows\\Dockerfile'
                //            label 'windows&&docker'
                //          }
                //    }
                //    steps {
                //
                //        bat "if not exist logs mkdir logs"
                //        powershell "& python.exe setup.py build -b ${WORKSPACE}\\build  | tee ${WORKSPACE}\\logs\\build.log"
                //    }
                //    post{
                //        always{
                //            archiveArtifacts artifacts: "logs/build.log"
                //        }
                //        failure{
                //            echo "Failed to build Python package"
                //        }
                //        success{
                //            echo "Successfully built project is ./build."
                //        }
                //    }
                //}
        stage("Sphinx Documentation"){
            agent {
              dockerfile {
                    filename 'ci\\docker\\windows\\Dockerfile'
                    label 'windows&&docker'
                  }
            }
            steps {
                echo "Building docs on ${env.NODE_NAME}"
                bat "if not exist logs mkdir logs"
                bat "sphinx-build.exe -b html ${WORKSPACE}\\docs\\source ${WORKSPACE}\\build\\docs\\html -d ${WORKSPACE}\\build\\docs\\doctrees -w ${WORKSPACE}\\logs\\build_sphinx.log"
            }
            post{
                always {
                    recordIssues(tools: [sphinxBuild(name: 'Sphinx Documentation Build', pattern: 'logs/build_sphinx.log')])
                    archiveArtifacts artifacts: 'logs/build_sphinx.log'
                }
                success{
                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                    unstash "DIST-INFO"
                    script{
                        def props = readProperties interpolate: true, file: 'uiucprescon_getmarc.dist-info/METADATA'
                        def DOC_ZIP_FILENAME = "${props.Name}-${props.Version}.doc.zip"
                        zip archive: true, dir: "build/docs/html", glob: '', zipFile: "dist/${DOC_ZIP_FILENAME}"
                    }
                    stash includes: 'build/docs/html/**', name: 'docs'
                }
                failure{
                    echo "Failed to build Python package"
                }
                cleanup{
                    cleanWs notFailBuild: true
                }
            }
        }
        stage("Testing") {

            stages{
                stage("Running Tests"){
                    parallel {
                        stage("Run Tox Test") {
                            when {
                                equals expected: true, actual: params.TEST_RUN_TOX
                            }
                            agent {
                              dockerfile {
                                    filename 'ci\\docker\\windows\\Dockerfile'
                                    label 'windows&&docker'
                                  }
                            }
                            steps {
                                script{
                                    try{
                                        bat (
                                            label: "Run Tox",
                                            script: "tox --parallel=auto --parallel-live --workdir ${WORKSPACE}\\.tox -v  -e py"
                                        )
                                    } catch (exc) {
                                        bat (
                                            label: "Run Tox with new environments",
                                            script: "tox --recreate --parallel=auto --parallel-live --workdir ${WORKSPACE}\\.tox -v -e py"
                                        )
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
                                            [pattern: 'logs/tox_report.json', type: 'INCLUDE']
                                        ]
                                    )
                                }
                            }
                        }
                        stage("Run Doctest Tests"){
                            agent {
                              dockerfile {
                                    filename 'ci\\docker\\windows\\Dockerfile'
                                    label 'windows&&docker'
                                  }
                            }
                            steps {
                                unstash "docs"
                                powershell "New-Item -ItemType Directory -Force -Path logs"
                                bat "sphinx-build.exe -b doctest docs\\source ${WORKSPACE}\\build\\docs -d ${WORKSPACE}\\build\\docs\\doctrees -w ${WORKSPACE}\\logs\\doctest.log"
                            }
                            post{
                                always {
                                    archiveArtifacts artifacts: "logs/doctest.log"

                                }
                            }
                        }
                        stage("Run MyPy Static Analysis") {
                            agent {
                                  dockerfile {
                                        filename 'ci/docker/linux/Dockerfile'
                                        label 'linux&&docker'
                                      }
                            }
                            steps{
                                sh "mkdir -p logs"
                                catchError(buildResult: "SUCCESS", message: 'MyPy found issues', stageResult: "UNSTABLE") {
                                    sh "mypy -p uiucprescon --html-report reports/mypy/html | tee logs/mypy.log"
                                }
                            }
                            post {
                                always {
                                    recordIssues(
                                        tools: [myPy(pattern: 'logs/mypy.log')]
                                        )
                                    archiveArtifacts artifacts: "logs/mypy.log"
                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy/html/', reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                                }
                            }
                        }
                        stage("Run Integration Tests") {
                            agent {
                                  dockerfile {
                                        filename 'ci\\docker\\windows\\Dockerfile'
                                        label 'windows&&docker'
                                  }
                            }
                            when {
                                equals expected: true, actual: params.TEST_RUN_INTEGRATION
                            }
                            steps {
                                bat "coverage run --source=uiucprescon -m pytest -m integration"
                                bat "coverage xml -o reports/integration_tests_coverage.xml"
//                                bat "pytest.exe -m integration --cov-report xml:${WORKSPACE}/reports/integration_tests_coverage.xml --cov=uiucprescon"
                            }
                            post {
                                success{
                                    stash includes: 'reports/integration_tests_coverage.xml', name: 'integration_tests_coverage'
                                }

                            }
                        }
                        stage("Run Unit Tests") {
                            agent {
                                  dockerfile {
                                        filename 'ci\\docker\\windows\\Dockerfile'
                                        label 'windows&&docker'
                                  }
                            }
                            steps {
                                bat "pytest.exe --cov-report xml:${WORKSPACE}/reports/unit_tests_coverage.xml --cov=uiucprescon"
                            }
                            post {
                                success{
                                    stash includes: 'reports/unit_tests_coverage.xml', name: 'unit_tests_coverage'
                                }
                            }
                        }
                    }
                }
                stage("Submit Coverage Report"){
                    agent any
                    steps{
                        unstash "unit_tests_coverage"
                        script{
                            try{
                                unstash "integration_tests_coverage"
                            } catch (Exception ex) {
                                echo "no integration test coverage file found"
                            }
                        }
                        publishCoverage adapters: [coberturaAdapter(mergeToOneReport: true, path: 'reports/*.xml')], sourceFileResolver: sourceFiles('STORE_ALL_BUILD')
                    }
                    post{
                        always{
                            archiveArtifacts artifacts: "reports/*.xml"
                        }
                    }
                }
            }

//                cleanup{
//                    bat "del reports\\coverage.xml"
//                    cleanWs notFailBuild: true
//                }
        }
    
        stage("Packaging") {
            agent {
              dockerfile {
                    filename 'ci\\docker\\windows\\Dockerfile'
                    label 'windows&&docker'
                  }
            }
            steps {
                bat "python.exe setup.py bdist_wheel sdist -d ${WORKSPACE}\\dist --format zip bdist_wheel -d ${WORKSPACE}\\dist"
            }

            post{
                success{
                    archiveArtifacts artifacts: "dist/*.whl,dist/*.tar.gz,dist/*.zip", fingerprint: true
                    stash includes: 'dist/*.*', name: "dist"
                }
                cleanup{
                    cleanWs(notFailBuild: true)
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
                DEVPI = credentials("DS_devpi")
            }
            stages{
                stage("Upload to DevPi Staging") {
                    agent {
                        dockerfile {
                            filename 'ci\\docker\\windows\\Dockerfile'
                            label 'windows&&docker'
                        }
                   }
                    steps {
                        bat "pip.exe install devpi-client"
                        unstash "dist"
                        devpiUpload(
                            devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                            url: "https://devpi.library.illinois.edu",
                            index: "${env.BRANCH_NAME}_staging",
                            distPath: "dist"
                            )
//                        bat "devpi.exe use https://devpi.library.illinois.edu"
//                        bat "devpi use https://devpi.library.illinois.edu && devpi login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} && devpi use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging && devpi upload --from-dir dist"
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
                                        unstash "DIST-INFO"
                                        script{
                                            def props = readProperties interpolate: true, file: 'uiucprescon_getmarc.dist-info/METADATA'

                                            devpiTest(
                                                devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                                                url: "https://devpi.library.illinois.edu",
                                                index: "${env.BRANCH_NAME}_staging",
                                                pkgName: "${props.Name}",
                                                pkgVersion: "${props.Version}",
                                                pkgRegex: "zip",
                                                detox: false
                                            )
                                        }
                                        echo "Finished testing Source Distribution: .zip"
                                    }

                                }
                            }

                            post {
                                cleanup{
                                    cleanWs notFailBuild: true
                                }
//                                cleanup{
//                                        cleanWs deleteDirs: true, patterns: [
//                                            [pattern: 'certs', type: 'INCLUDE']
//                                        ]
//                                    }
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
                                        unstash "DIST-INFO"
                                        script{
                                            def props = readProperties interpolate: true, file: 'uiucprescon_getmarc.dist-info/METADATA'
                                            devpiTest(
    //                                                devpiExecutable: "venv\\36\\Scripts\\devpi.exe",
                                                devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                                                url: "https://devpi.library.illinois.edu",
                                                index: "${env.BRANCH_NAME}_staging",
                                                pkgName: "${props.Name}",
                                                pkgVersion: "${props.Version}",
                                                pkgRegex: "whl",
                                                detox: false
                                                )
                                        }

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
                        unstash "DIST-INFO"
                        script {
                            def props = readProperties interpolate: true, file: 'uiucprescon_getmarc.dist-info/METADATA'
                            input "Release ${props.Name} ${props.Version} to DevPi Production?"
                            bat "venv\\36\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW}"

                            bat "venv\\36\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
                            bat "venv\\36\\Scripts\\devpi.exe push ${props.Name}==${props.Version} production/release"
                        }
                    }
                }
            }
            post {
                success {
                    echo "it Worked. Pushing file to ${env.BRANCH_NAME} index"
                    unstash "DIST-INFO"
                    script{
                        def props = readProperties interpolate: true, file: 'uiucprescon_getmarc.dist-info/METADATA'
                        bat "venv\\36\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW}"
                        bat "venv\\36\\Scripts\\devpi.exe use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging"
                        bat "venv\\36\\Scripts\\devpi.exe push ${props.Name}==${props.Version} ${env.DEVPI_USR}/${env.BRANCH_NAME}"

                    }

                }
                failure {
                    echo "At least one package format on DevPi failed."
                }
                cleanup{
                    unstash "DIST-INFO"
                    script{
                        def props = readProperties interpolate: true, file: 'uiucprescon_getmarc.dist-info/METADATA'
                        remove_from_devpi("venv\\36\\Scripts\\devpi.exe", "${props.Name}", "${props.Version}", "/${env.DEVPI_USR}/${env.BRANCH_NAME}_staging", "${env.DEVPI_USR}", "${env.DEVPI_PSW}")
                    }
                    cleanWs notFailBuild: true
                }
            }
        }
        stage("Deploy"){
            parallel {
                stage("Deploy Online Documentation") {
                    when{
                        equals expected: true, actual: params.DEPLOY_DOCS
                    }
                    agent any
                    steps{
                        unstash "docs"
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
                    post{
                        cleanup{
                            deleteDir()
//                            cleanWs notFailBuild: true
                        }
                    }
                }

            }
        }
    }
}

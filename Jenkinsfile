#!groovy
@Library(["devpi", "PythonHelpers"]) _


def CONFIGURATIONS = [
    "3.6": [
            package_testing: [
                whl: [
                    pkgRegex: "*.whl",
                ],
                sdist: [
                    pkgRegex: "*.zip",
                ]
            ],
            test_docker_image: "python:3.6-windowsservercore",
            tox_env: "py36",
            devpi_wheel_regex: "cp36"

        ],
    "3.7": [
            package_testing: [
                whl: [
                    pkgRegex: "*.whl",
                ],
                sdist:[
                    pkgRegex: "*.zip",
                ]
            ],
            test_docker_image: "python:3.7",
            tox_env: "py37",
            devpi_wheel_regex: "cp37"
        ],
    "3.8": [
            package_testing: [
                whl: [
                    pkgRegex: "*.whl",
                ],
                sdist:[
                    pkgRegex: "*.zip",
                ]
            ],
            test_docker_image: "python:3.8",
            tox_env: "py38",
            devpi_wheel_regex: "cp38"
        ]
]

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
    environment {
        build_number = VersionNumber(projectStartDate: '2018-3-27', versionNumberString: '${BUILD_DATE_FORMATTED, "yy"}${BUILD_MONTH, XX}${BUILDS_THIS_MONTH, XX}', versionPrefix: '', worstResultForIncrement: 'SUCCESS')
    }
    parameters {
        booleanParam(name: "FRESH_WORKSPACE", defaultValue: false, description: "Purge workspace before staring and checking out source")
        string(name: "PROJECT_NAME", defaultValue: "pyGetMarc", description: "Name given to the project")
//         booleanParam(name: "TEST_RUN_INTEGRATION", defaultValue: true, description: "Run integration tests")
        booleanParam(name: "TEST_RUN_TOX", defaultValue: false, description: "Run Tox Tests")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpy.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to https://devpi.library.illinois.edu/production/release")
        string(name: 'URL_SUBFOLDER', defaultValue: "pygetmarc", description: 'The directory that the docs should be saved under')
    }
    stages {
        stage("Getting Distribution Info"){
               agent {
                    dockerfile {
                        filename 'ci/docker/linux/Dockerfile'
                        label 'linux && docker'
                    }
                }
                steps{
                    sh(
                        label: "Creating dist_info",
                        script: "python setup.py dist_info"
                        )
                }
                post{
                    success{
                        stash includes: "uiucprescon_getmarc.dist-info/**", name: 'DIST-INFO'
                        archiveArtifacts artifacts: "uiucprescon_getmarc.dist-info/**"
                    }
                }
            }
        stage("Sphinx Documentation"){
            agent {
                dockerfile {
                    filename 'ci/docker/linux/Dockerfile'
                    label 'linux && docker'
                }
            }
            steps {
                timeout(3){
                    sh(label:"Building docs on ${env.NODE_NAME}",
                       script: """mkdir -p logs
                       python -m sphinx -b html docs/source build/docs/html -dbuild/docs/doctrees -w logs/build_sphinx.log
                       """
                       )
                }
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
                        stash includes: "dist/${DOC_ZIP_FILENAME},build/docs/html/**", name: 'DOCS_ARCHIVE'
                    }

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
                                    filename 'ci/docker/linux/Dockerfile'
                                    label 'linux && docker'
                                }
                            }
                            steps {
                                timeout(3){
                                    sh "tox -e py"
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
                                    filename 'ci/docker/linux/Dockerfile'
                                    label 'linux && docker'
                                }
                            }
                            options{
                                retry(2)
                            }
                            steps {
                                timeout(3){
                                    unstash "DOCS_ARCHIVE"
                                    sh(label: "Running Run Doctest",
                                        script: """mkdir -p logs
                                               coverage run -p -m sphinx -b doctest docs/source build/docs -d build/docs/doctrees -w logs/doctest.log
                                               """
                                               )
                                }
                            }
                            post{
                                always {
                                    stash includes: '.coverage.*', name: 'doctest_coverage'
                                }
                                cleanup{
                                    cleanWs notFailBuild: true
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
                                timeout(3){
                                    catchError(buildResult: "SUCCESS", message: 'MyPy found issues', stageResult: "UNSTABLE") {
                                        sh(label: "Running MyPy",
                                           script: """mkdir -p logs
                                                      mypy -p uiucprescon --html-report reports/mypy/html | tee logs/mypy.log
                                                      """
                                        )
                                    }
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
                                cleanup{
                                    cleanWs notFailBuild: true
                                }
                            }
                        }
//                         stage("Run Integration Tests") {
//                             agent {
//                                   dockerfile {
//                                         filename 'ci/docker/linux/Dockerfile'
//                                         label 'linux&&docker'
//                                       }
//                             }
// //                             agent {
// //                                   dockerfile {
// //                                         filename 'ci\\docker\\windows\\Dockerfile'
// //                                         label 'windows&&docker'
// //                                   }
// //                             }
//                             when {
//                                 equals expected: true, actual: params.TEST_RUN_INTEGRATION
//                             }
//                             options{
//                                 retry(2)
//                             }
//                             steps {
//                                 timeout(3){
//                                     sh(label: "Running pytest with integration",
//                                        script: """coverage run -p --source=uiucprescon -m pytest -m integration"""
//                                    )
// //                                     bat "coverage run -p --source=uiucprescon -m pytest -m integration"
//                                 }
//                             }
//                             post {
//                                 success{
//                                     stash includes: '.coverage.*', name: 'integration_tests_coverage'
//                                 }
//                                 cleanup{
//                                     cleanWs notFailBuild: true
//                                 }
//
//                             }
//                         }
                        stage("Run Unit Tests") {
//                             agent {

//                                   dockerfile {
//                                         filename 'ci\\docker\\windows\\Dockerfile'
//                                         label 'windows&&docker'
//                                   }
//                             }
                            agent {
                                  dockerfile {
                                        filename 'ci/docker/linux/Dockerfile'
                                        label 'linux&&docker'
                                      }
                            }
                            steps {
                                timeout(3){
                                    catchError(buildResult: "UNSTABLE", message: 'pytest found issues', stageResult: "UNSTABLE") {
                                        sh "coverage run -p --source=uiucprescon -m pytest --junitxml=reports/pytest.xml"
                                    }
    //                                     bat "coverage run -p --source=uiucprescon -m pytest"

                                }
                            }
                            post {
                                always{
                                    junit "reports/pytest.xml"
                                    stash includes: '.coverage.*', name: 'unit_tests_coverage'
                                }
                                cleanup{
                                    cleanWs notFailBuild: true
                                }
                            }
                        }
                    }
                }
                stage("Submit Coverage Report"){
                    agent {
                          dockerfile {
                                filename 'ci/docker/linux/Dockerfile'
                                label 'linux&&docker'
                              }
                    }
                    steps{
                        timeout(3){
                            unstash "unit_tests_coverage"
                            unstash "doctest_coverage"
                            sh(label:"combining coverage",
                               script: """coverage combine
                                          coverage xml -i -o reports/coverage.xml
                                          """
                            )
                            publishCoverage adapters: [coberturaAdapter(mergeToOneReport: true, path: 'reports/*.xml')], sourceFileResolver: sourceFiles('STORE_ALL_BUILD'), tag: "coverage"
                        }
                    }
                    post{
                        always{
                            archiveArtifacts artifacts: "reports/*.xml"
                        }
                        cleanup{
                            cleanWs notFailBuild: true
                        }
                    }
                }
            }
        }
    
        stage("Packaging") {
//             agent {
//               dockerfile {
//                     filename 'ci\\docker\\windows\\Dockerfile'
//                     label 'windows&&docker'
//                   }
//             }
            agent {
                  dockerfile {
                        filename 'ci/docker/linux/Dockerfile'
                        label 'linux&&docker'
                      }
            }
            steps {
                timeout(3){
                    sh "python setup.py bdist_wheel sdist -d dist --format zip bdist_wheel -d dist"
                }
//                 bat "python.exe setup.py bdist_wheel sdist -d ${WORKSPACE}\\dist --format zip bdist_wheel -d ${WORKSPACE}\\dist"
            }

            post{
                success{
                    archiveArtifacts artifacts: "dist/*.whl,dist/*.tar.gz,dist/*.zip", fingerprint: true
                }
                always{
                    stash includes: 'dist/*.*', name: "dist"
                }
                cleanup{
                    cleanWs(notFailBuild: true)
                }
            }
        }

//         stage("Deploying to DevPi") {
//            when {
//                 allOf{
//                     anyOf{
//                         equals expected: true, actual: params.DEPLOY_DEVPI
//                         triggeredBy "TimerTriggerCause"
//                     }
//                     anyOf {
//                         equals expected: "master", actual: env.BRANCH_NAME
//                         equals expected: "dev", actual: env.BRANCH_NAME
//                     }
//                 }
//                 beforeAgent true
//            }
//            options{
//                 timestamps()
//                 lock("pygetmarc-devpi")
//            }
//            agent {
//                 label "windows && Python3"
//            }
//
//             environment{
//                 DEVPI = credentials("DS_devpi")
//             }
//             stages{
//                 stage("Installing DevPi Client"){
//                     environment{
//                         PATH = "${tool 'CPython-3.7'};$PATH"
//                     }
//                     steps{
//                         bat "python -m venv venv"
//                         bat "venv\\Scripts\\pip.exe install devpi-client"
//                     }
//                 }
//                 stage("Upload to DevPi Staging") {
//                     environment{
//                         PATH = "${WORKSPACE}\\venv\\Scripts;$PATH"
//                     }
//                     steps {
//                         unstash "dist"
//                         devpiUpload(
//                             devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
//                             url: "https://devpi.library.illinois.edu",
//                             index: "${env.BRANCH_NAME}_staging",
//                             distPath: "dist"
//                             )
//                     }
//                 }
//                 stage("Test DevPi Packages") {
//                     parallel {
//                         stage("Source Distribution: .zip") {
//                             agent {
//                                 node {
//                                     label "Windows && Python3"
//                                 }
//                             }
//                             options {
//                                 skipDefaultCheckout(true)
//                             }
//
//                             stages{
//                                 stage("Building DevPi Testing venv for .zip Package"){
//                                     environment {
//                                         PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
//                                     }
//                                     steps{
//                                         lock("system_python_${NODE_NAME}"){
//                                             bat "python -m venv venv"
//                                         }
//                                         bat "venv\\Scripts\\python.exe -m pip install pip --upgrade && venv\\Scripts\\pip.exe install setuptools --upgrade && venv\\Scripts\\pip.exe install \"tox<3.7\" detox devpi-client"
//                                     }
//                                 }
//                                 stage("Testing DevPi zip Package"){
//                                     options{
//                                         timeout(20)
//                                     }
//                                     environment {
//                                         PATH = "${WORKSPACE}\\venv\\Scripts;${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
//                                     }
//                                     steps {
//                                         echo "Testing Source tar.gz package in devpi"
//                                         unstash "DIST-INFO"
//                                         script{
//                                             def props = readProperties interpolate: true, file: 'uiucprescon_getmarc.dist-info/METADATA'
//
//                                             devpiTest(
//                                                 devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
//                                                 url: "https://devpi.library.illinois.edu",
//                                                 index: "${env.BRANCH_NAME}_staging",
//                                                 pkgName: "${props.Name}",
//                                                 pkgVersion: "${props.Version}",
//                                                 pkgRegex: "zip",
//                                                 detox: false
//                                             )
//                                         }
//                                         echo "Finished testing Source Distribution: .zip"
//                                     }
//
//                                 }
//                             }
//
//                             post {
//                                 cleanup{
//                                     cleanWs notFailBuild: true
//                                 }
//                             }
//
//                         }
//                         stage("Built Distribution: .whl") {
//                             agent {
//                                 node {
//                                     label "Windows && Python3"
//                                 }
//                             }
//                             environment {
//                                 PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.6'}\\Scripts;${tool 'CPython-3.7'};$PATH"
//                             }
//                             options {
//                                 skipDefaultCheckout(true)
//                             }
//                             stages{
//                                 stage("Creating venv to Test Whl"){
//                                     steps {
//                                         lock("system_python_${NODE_NAME}"){
//                                             bat "if not exist venv\\36 mkdir venv\\36"
//                                             bat "\"${tool 'CPython-3.6'}\\python.exe\" -m venv venv\\36"
//                                             bat "if not exist venv\\37 mkdir venv\\37"
//                                             bat "\"${tool 'CPython-3.7'}\\python.exe\" -m venv venv\\37"
//                                         }
//                                         bat "venv\\36\\Scripts\\python.exe -m pip install pip --upgrade && venv\\36\\Scripts\\pip.exe install setuptools --upgrade && venv\\36\\Scripts\\pip.exe install \"tox<3.7\" devpi-client"
//                                     }
//
//                                 }
//                                 stage("Testing DevPi .whl Package"){
//                                     options{
//                                         timeout(20)
//                                     }
//                                     environment{
//                                        PATH = "${WORKSPACE}\\venv\\36\\Scripts;${tool 'CPython-3.6'};${tool 'CPython-3.6'}\\Scripts;${tool 'CPython-3.7'};$PATH"
//                                     }
//                                     steps {
//                                         echo "Testing Whl package in devpi"
//                                         unstash "DIST-INFO"
//                                         script{
//                                             def props = readProperties interpolate: true, file: 'uiucprescon_getmarc.dist-info/METADATA'
//                                             devpiTest(
//                                                 devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
//                                                 url: "https://devpi.library.illinois.edu",
//                                                 index: "${env.BRANCH_NAME}_staging",
//                                                 pkgName: "${props.Name}",
//                                                 pkgVersion: "${props.Version}",
//                                                 pkgRegex: "whl",
//                                                 detox: false
//                                                 )
//                                         }
//
//                                         echo "Finished testing Built Distribution: .whl"
//                                     }
//                                 }
//
//                             }
//                         }
//                     }
//                 }
//                 stage("Deploy to DevPi Production") {
//                     when {
//                         allOf{
//                             equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
//                             branch "master"
//                         }
//                     }
//                     agent {
//                         dockerfile {
//                             filename 'ci\\docker\\windows\\Dockerfile'
//                             label 'windows&&docker'
//                         }
//                    }
//                     steps {
//                         bat "pip.exe install devpi-client"
//                         unstash "DIST-INFO"
//                         script {
//                             def props = readProperties interpolate: true, file: 'uiucprescon_getmarc.dist-info/METADATA'
//                             input "Release ${props.Name} ${props.Version} to DevPi Production?"
//                             bat "venv\\36\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW}"
//
//                             bat "venv\\36\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
//                             bat "venv\\36\\Scripts\\devpi.exe push ${props.Name}==${props.Version} production/release"
//                         }
//                     }
//                 }
//             }
//             post {
//                 success {
//                     echo "it Worked. Pushing file to ${env.BRANCH_NAME} index"
//                     unstash "DIST-INFO"
//                     script{
//                         def props = readProperties interpolate: true, file: 'uiucprescon_getmarc.dist-info/METADATA'
//                         bat "venv\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW}"
//                         bat "venv\\Scripts\\devpi.exe use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging"
//                         bat "venv\\Scripts\\devpi.exe push ${props.Name}==${props.Version} ${env.DEVPI_USR}/${env.BRANCH_NAME}"
//
//                     }
//
//                 }
//                 failure {
//                     echo "At least one package format on DevPi failed."
//                 }
//                 cleanup{
//                     unstash "DIST-INFO"
//                     script{
//                         def props = readProperties interpolate: true, file: 'uiucprescon_getmarc.dist-info/METADATA'
//                         remove_from_devpi("venv\\Scripts\\devpi.exe", "${props.Name}", "${props.Version}", "/${env.DEVPI_USR}/${env.BRANCH_NAME}_staging", "${env.DEVPI_USR}", "${env.DEVPI_PSW}")
//                     }
//                     cleanWs notFailBuild: true
//                 }
//             }
//         }
        stage("Deploy to DevPi") {
            when {
                allOf{
                    anyOf{
                        equals expected: true, actual: params.DEPLOY_DEVPI
                    }
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
                beforeAgent true
            }
            options{
                timestamps()
                lock("pygetmarc-devpi")
            }
            environment{
                DEVPI = credentials("DS_devpi")
            }
            stages{
                stage("Deploy to Devpi Staging") {
                    agent {
                        dockerfile {
                            filename 'ci/docker/devpi/deploy/Dockerfile'
                            label 'linux&&docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                          }
                    }
                    steps {
                        unstash 'DOCS_ARCHIVE'
                        unstash 'dist'
                        sh(
                                label: "Connecting to DevPi Server",
                                script: 'devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi && devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi'
                            )
                        sh(
                            label: "Uploading to DevPi Staging",
                            script: """devpi use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}/devpi
devpi upload --from-dir dist --clientdir ${WORKSPACE}/devpi"""
                        )
                    }
                    post{
                        cleanup{
                            cleanWs(
                                deleteDirs: true,
                                patterns: [
                                    [pattern: "dist/", type: 'INCLUDE'],
                                    [pattern: "devpi/", type: 'INCLUDE'],
                                    [pattern: 'build/', type: 'INCLUDE']
                                ]
                            )
                        }
                    }
                }
                stage("Test DevPi packages") {
                    matrix {
                        axes {
                            axis {
                                name 'FORMAT'
                                values 'zip', "whl"
                            }
                            axis {
                                name 'PYTHON_VERSION'
                                values '3.6', "3.7", "3.8"
                            }
                        }
                        agent {
                          dockerfile {
                            additionalBuildArgs "--build-arg PYTHON_DOCKER_IMAGE_BASE=${CONFIGURATIONS[PYTHON_VERSION].test_docker_image}"
                            filename 'ci/docker/devpi/test/windows/Dockerfile'
                            label 'windows && docker'
                          }
                        }
                        stages{
                            stage("Testing DevPi Package"){
                                options{
                                    timeout(10)
                                }
                                steps{
                                    script{
                                        unstash "DIST-INFO"
                                        def props = readProperties interpolate: true, file: 'uiucprescon_getmarc.dist-info/METADATA'
                                        bat(
                                            label: "Connecting to Devpi Server",
                                            script: "devpi use https://devpi.library.illinois.edu --clientdir certs\\ && devpi login %DEVPI_USR% --password %DEVPI_PSW% --clientdir certs\\ && devpi use ${env.BRANCH_NAME}_staging --clientdir certs\\"
                                        )
                                        bat(
                                            label: "Testing ${FORMAT} package stored on DevPi with Python version ${PYTHON_VERSION}",
                                            script: "devpi test --index ${env.BRANCH_NAME}_staging ${props.Name}==${props.Version} -s ${FORMAT} --clientdir certs\\ -e ${CONFIGURATIONS[PYTHON_VERSION].tox_env} -v"
                                        )
                                    }
                                }
                                post{
                                    cleanup{
                                        cleanWs(
                                            deleteDirs: true,
                                            patterns: [
                                                [pattern: "dist/", type: 'INCLUDE'],
                                                [pattern: "certs/", type: 'INCLUDE'],
                                                [pattern: 'build/', type: 'INCLUDE']
                                            ]
                                        )
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
                        beforeAgent true
                    }
                    agent {
                        dockerfile {
                            filename 'ci/docker/devpi/deploy/Dockerfile'
                            label 'linux&&docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                          }
                    }
                    input {
                        message 'Release to DevPi Production?'
                    }
                    steps {
                        unstash "DIST-INFO"
                        script{
                            def props = readProperties interpolate: true, file: "uiucprescon_getmarc.dist-info/METADATA"
                            sh(
                                label: "Pushing to DS_Jenkins/${env.BRANCH_NAME} index",
                                script: """devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi
                                           devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi
                                           devpi push --index DS_Jenkins/${env.BRANCH_NAME}_staging ${props.Name}==${props.Version} production/release --clientdir ${WORKSPACE}/devpi"""
                            )
                        }
                    }
                }
            }
            post{
                success{
                    node('linux && docker') {
                       script{
                            docker.build("pygetmarc:devpi.${env.BUILD_ID}",'-f ./ci/docker/devpi/deploy/Dockerfile --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .').inside{
                                unstash "DIST-INFO"
                                def props = readProperties interpolate: true, file: 'uiucprescon_getmarc.dist-info/METADATA'
                                sh(
                                    label: "Connecting to DevPi Server",
                                    script: 'devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi && devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi'
                                )
                                sh(
                                    label: "Selecting to DevPi index",
                                    script: "devpi use /DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}/devpi"
                                )
                                sh(
                                    label: "Pushing package to DevPi index",
                                    script:  "devpi push ${props.Name}==${props.Version} DS_Jenkins/${env.BRANCH_NAME} --clientdir ${WORKSPACE}/devpi"
                                )
                            }
                       }
                    }
                }
                cleanup{
                    node('linux && docker') {
                       script{
                            docker.build("pygetmarc:devpi.${env.BUILD_ID}",'-f ./ci/docker/devpi/deploy/Dockerfile --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .').inside{
                                unstash "DIST-INFO"
                                def props = readProperties interpolate: true, file: 'uiucprescon_getmarc.dist-info/METADATA'
                                sh(
                                    label: "Connecting to DevPi Server",
                                    script: 'devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi && devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi'
                                )
                                sh(
                                    label: "Selecting to DevPi index",
                                    script: "devpi use /DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}/devpi"
                                )
                                sh(
                                    label: "Removing package to DevPi index",
                                    script: "devpi remove -y ${props.Name}==${props.Version} --clientdir ${WORKSPACE}/devpi"
                                )
                                cleanWs(
                                    deleteDirs: true,
                                    patterns: [
                                        [pattern: "dist/", type: 'INCLUDE'],
                                        [pattern: "devpi/", type: 'INCLUDE'],
                                        [pattern: "uiucprescon.packager.dist-info/", type: 'INCLUDE'],
                                        [pattern: 'build/', type: 'INCLUDE']
                                    ]
                                )
                            }
                       }
                    }
                }
            }
        }
        stage("Deploy"){
            parallel {
                stage("Deploy Online Documentation") {
                    when{
                        equals expected: true, actual: params.DEPLOY_DOCS
                        beforeAgent true
                    }
                    agent any
                    options {
                        skipDefaultCheckout(true)
                    }
                    steps{
                        unstash "DOCS_ARCHIVE"
                        dir("build/docs/html/"){
                            input 'Update project documentation?'
                            sshPublisher(
                                publishers: [
                                    sshPublisherDesc(
                                        configName: 'apache-ns - lib-dccuser-updater', 
                                        sshLabel: [label: 'Linux && !aws'],
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
                        }
                    }
                }

            }
        }
    }
}

#!groovy
@Library("ds-utils@v0.2.0") // Uses library from https://github.com/UIUCLibrary/Jenkins_utils
import org.ds.*

def name = "unknown"
def version = "unknown"

def reports_dir = ""

pipeline {
    agent {
        label "Windows&&DevPi"
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
        booleanParam(name: "TEST_RUN_FLAKE8", defaultValue: true, description: "Run Flake8 static analysis")
        booleanParam(name: "TEST_RUN_MYPY", defaultValue: true, description: "Run MyPy static analysis")
        booleanParam(name: "TEST_RUN_TOX", defaultValue: true, description: "Run Tox Tests")
        booleanParam(name: "ADDITIONAL_TESTS", defaultValue: true, description: "Run additional tests")
        booleanParam(name: "PACKAGE", defaultValue: true, description: "Create a package")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: true, description: "Deploy to devpi on http://devpy.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        choice(choices: 'None\nRelease_to_devpi_only\nRelease_to_devpi_and_sccm\n', description: "Release the build to production. Only available in the Master branch", name: 'RELEASE')
        booleanParam(name: "UPDATE_DOCS", defaultValue: false, description: "Update online documentation")
        string(name: 'URL_SUBFOLDER', defaultValue: "pygetmarc", description: 'The directory that the docs should be saved under')
    }
    stages 
    {
        stage("Configure") {
            steps {
                // Set up the reports directory variable 
                script{
                    reports_dir = "${pwd tmp: true}\\reports"
                }
                
                script{
                    if (params.FRESH_WORKSPACE == true){
                        deleteDir()
                        checkout scm
                    }
                }

                dir(pwd(tmp: true)){
                    dir("logs"){
                        deleteDir()
                    }
                
                }
                dir("logs"){
                    deleteDir()
                }
                
                dir("build"){
                    deleteDir()
                    echo "Cleaned out build directory"
                    bat "dir"
                }
                dir("${pwd tmp: true}/reports"){
                    deleteDir()
                    echo "Cleaned out reports directory"
                    bat "dir"
                }
                lock("system_python"){
                    bat "${tool 'CPython-3.6'} -m pip install --upgrade pip --quiet"
                }

                bat "dir"
                bat "dir source"

                script {
                    dir("source"){
                        name = bat(returnStdout: true, script: "@${tool 'CPython-3.6'}  setup.py --name").trim()
                        version = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --version").trim()
                    }
                }

                tee("${pwd tmp: true}/logs/pippackages_system_${NODE_NAME}.log") {
                    bat "${tool 'CPython-3.6'} -m pip list"
                }
                bat "dir ${pwd tmp: true}"
                bat "dir ${pwd tmp: true}\\logs"
                
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

                tee("${pwd tmp: true}/logs/pippackages_venv_${NODE_NAME}.log") {
                    bat "venv\\Scripts\\pip.exe list"
                }
                bat "venv\\Scripts\\devpi use https://devpi.library.illinois.edu"
                withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {    
                    bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                }
                bat "dir"
            }
            post{
                always{
                    echo """Name               = ${name}
Version            = ${version}
Report Directory   = ${reports_dir}
"""
                    

                    dir(pwd(tmp: true)){
                        archiveArtifacts artifacts: "logs/pippackages_system_${NODE_NAME}.log"
                        archiveArtifacts artifacts: "logs/pippackages_venv_${NODE_NAME}.log"

                    }
                }
                failure {
                    deleteDir()
                }
            }

        }

        // stage("Cloning Source") {
        //     steps {
        //         deleteDir()
        //         checkout scm
        //         stash includes: '**', name: "Source", useDefaultExcludes: false
        //     }

        // }
        stage('Build') {
            parallel {
                stage("Python Package"){
                    steps {
                        
                        tee('logs/build.log') {
                            dir("source"){
                                bat script: "${WORKSPACE}\\venv\\Scripts\\python.exe setup.py build -b ${WORKSPACE}\\build"

                                // powershell "Start-Process -NoNewWindow -FilePath ${tool 'CPython-3.6'} -ArgumentList '-m pipenv run python setup.py build -b ${WORKSPACE}\\build' -Wait"
                                // bat script: "${tool 'CPython-3.6'} -m pipenv run python setup.py build -b ${WORKSPACE}\\build"
                            }
                        }
                    }
                    post{
                        always{
                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'Pep8', pattern: 'logs/build.log']]
                            archiveArtifacts artifacts: "logs/*.log"
                            // bat "dir build"
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
                        // bat 'mkdir "build/docs/html"'
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
                            bat "${WORKSPACE}\\venv\\Scripts\\tox.exe --workdir ${WORKSPACE}\\.tox"
                        }
                        
                    }
                    post {
                        failure {
                            bat "@RD /S /Q ${WORKSPACE}\\.tox"
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

            }
        }
        
        stage("Additional tests") {
            when {
                expression { params.ADDITIONAL_TESTS == true }
            }

            steps {
                parallel(
                    "Documentation": {
                        // node(label: "Windows") {
                        //     checkout scm
                        dir("source"){
                            // bat "${WORKSPACE}\\venv\\Scripts\\tox.exe -e docs --workdir ${WORKSPACE}\\.tox"
                            bat "${WORKSPACE}\\venv\\Scripts\\sphinx-build.exe -b doctest ${WORKSPACE}\\source\\docs\\source ${WORKSPACE}\\build\\docs -d ${WORKSPACE}\\build\\docs\\doctrees"
                        }
                        bat "move build\\docs\\output.txt ${reports_dir}\\doctest.txt"                  
                        dir("${reports_dir}"){
                            bat "dir"
                            archiveArtifacts artifacts: "doctest.txt"
                        }
                        
                        // }
                    },
                    "MyPy": {
                    
                        // node(label: "Windows") {
                        //     checkout scm
                        dir("source"){
                            // bat "call make.bat install-dev"
                            bat "${WORKSPACE}\\venv\\Scripts\\mypy.exe -p uiucprescon --junit-xml=junit-${env.NODE_NAME}-mypy.xml --html-report ${WORKSPACE}//reports/mypy_html"
                            junit "junit-${env.NODE_NAME}-mypy.xml"
                            
                        }
                        publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy_html', reportFiles: 'index.html', reportName: 'MyPy', reportTitles: ''])
                        // }
                    },
                    "Integration": {
                        // node(label: "Windows"){
                            // checkout scm
                        dir("source"){
                            // bat "call make.bat install-dev"
                            bat "${WORKSPACE}\\venv\\Scripts\\pip.exe install pytest-cov"
                            bat "${WORKSPACE}\\venv\\Scripts\\pytest.exe -m integration --junitxml=${WORKSPACE}/reports/junit-${env.NODE_NAME}-pytest.xml --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/coverage/ --cov=uiucprescon"
                        }
                        publishHTML([allowMissing: true, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/coverage', reportFiles: 'index.html', reportName: 'Coverage-integration', reportTitles: ''])
                        // }
                    }
                )
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
                }
            }
        }
        // stag
        // stage("Packaging") {
        //     when {
        //         expression { params.PACKAGE == true }
        //     }
            

        //     // steps {
        //     //     parallel(
        //     //             "Source and Wheel formats": {
        //     //                 dir("source"){
        //     //                     bat "call make.bat"
        //     //                 }
        //     //             },
        //     //     )
        //     // }
        //     post {
        //       success {
        //           dir("source"){
        //             dir("dist"){
        //                 archiveArtifacts artifacts: "*.whl", fingerprint: true
        //                 archiveArtifacts artifacts: "*.tar.gz", fingerprint: true
        //             }
        //         }
        //       }
        //     }

        // }

        stage("Deploying to Devpi") {
            when {
                expression { params.DEPLOY_DEVPI == true && (env.BRANCH_NAME == "master" || env.BRANCH_NAME == "dev") }
            }
            steps {
                bat "${tool 'CPython-3.6'} -m devpi use http://devpy.library.illinois.edu"
                withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                    bat "${tool 'CPython-3.6'} -m devpi login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                    bat "${tool 'CPython-3.6'} -m devpi use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                    script {
                        bat "${tool 'CPython-3.6'} -m devpi upload --from-dir dist"
                        try {
                            bat "${tool 'CPython-3.6'} -m devpi upload --only-docs --from-dir dist"
                        } catch (exc) {
                            echo "Unable to upload to devpi with docs."
                        }
                    }
                }

            }
        }
        stage("Test Devpi packages") {
            when {
                expression { params.DEPLOY_DEVPI == true && (env.BRANCH_NAME == "master" || env.BRANCH_NAME == "dev") }
            }
            steps {
                parallel(
                        "Source": {
                            script {
                                // def name = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --name").trim()
                                // def version = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --version").trim()
                                node("Windows") {
                                    withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                                        bat "${tool 'CPython-3.6'} -m devpi login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                                        bat "${tool 'CPython-3.6'} -m devpi use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                                        echo "Testing Source package in devpi"
                                        bat "${tool 'CPython-3.6'} -m devpi test --index http://devpy.library.illinois.edu/${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging ${name} -s tar.gz"
                                    }
                                }

                            }
                        },
                        "Wheel": {
                            script {
                                // def name = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --name").trim()
                                // def version = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --version").trim()
                                node("Windows") {
                                    withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                                        bat "${tool 'CPython-3.6'} -m devpi login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                                        bat "${tool 'CPython-3.6'} -m devpi use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                                        echo "Testing Whl package in devpi"
                                        bat " ${tool 'CPython-3.6'} -m devpi test --index http://devpy.library.illinois.edu/${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging ${name} -s whl"
                                    }
                                }

                            }
                        }
                )

            }
            post {
                success {
                    echo "It Worked. Pushing file to ${env.BRANCH_NAME} index"
                    script {
                        // def name = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --name").trim()
                        // def version = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --version").trim()
                        withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                            bat "${tool 'CPython-3.6'} -m devpi login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                            bat "${tool 'CPython-3.6'} -m devpi use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                            bat "${tool 'CPython-3.6'} -m devpi push ${name}==${version} ${DEVPI_USERNAME}/${env.BRANCH_NAME}"
                        }

                    }
                }
            }
        }
        stage("Release to DevPi production") {
            when {
                expression { params.RELEASE != "None" && env.BRANCH_NAME == "master" }
            }

            steps {
                script {
                    // def name = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --name").trim()
                    // def version = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --version").trim()
                    withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                        bat "${tool 'CPython-3.6'} -m devpi login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                        bat "${tool 'CPython-3.6'} -m devpi use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                        bat "${tool 'CPython-3.6'} -m devpi push ${name}==${version} production/release"
                    }

                }
            }
            // post {
            //     success {
            //         build job: 'speedwagon/master', parameters: [string(nama: 'PROJECT_NAME', value: 'Speedwagon'), booleanParam(name: 'UPDATE_JIRA_EPIC', value: false), string(name: 'JIRA_ISSUE', value: 'PSR-83'), booleanParam(name: 'TEST_RUN_PYTEST', value: true), booleanParam(name: 'TEST_RUN_BEHAVE', value: true), booleanParam(name: 'TEST_RUN_DOCTEST', value: true), booleanParam(name: 'TEST_RUN_FLAKE8', value: true), booleanParam(name: 'TEST_RUN_MYPY', value: true), booleanParam(name: 'PACKAGE_PYTHON_FORMATS', value: true), booleanParam(name: 'PACKAGE_WINDOWS_STANDALONE', value: true), booleanParam(name: 'DEPLOY_DEVPI', value: true), string(name: 'RELEASE', value: 'None'), booleanParam(name: 'UPDATE_DOCS', value: false), string(name: 'URL_SUBFOLDER', value: 'speedwagon')], wait: false
            //     }
            // }
        }
        stage("Update online documentation") {
            agent {
                label "Linux"
            }
            when {
              expression {params.UPDATE_DOCS == true }
            }

            steps {
                updateOnlineDocs url_subdomain: params.URL_SUBFOLDER, stash_name: "HTML Documentation"
            }
        }
    }
    post {
        success {
            build job: 'speedwagon/master', parameters: [string(nama: 'PROJECT_NAME', value: 'Speedwagon'), booleanParam(name: 'UPDATE_JIRA_EPIC', value: false), string(name: 'JIRA_ISSUE', value: 'PSR-83'), booleanParam(name: 'TEST_RUN_PYTEST', value: true), booleanParam(name: 'TEST_RUN_BEHAVE', value: true), booleanParam(name: 'TEST_RUN_DOCTEST', value: true), booleanParam(name: 'TEST_RUN_FLAKE8', value: true), booleanParam(name: 'TEST_RUN_MYPY', value: true), booleanParam(name: 'PACKAGE_PYTHON_FORMATS', value: true), booleanParam(name: 'PACKAGE_WINDOWS_STANDALONE', value: true), booleanParam(name: 'DEPLOY_DEVPI', value: true), string(name: 'RELEASE', value: 'None'), booleanParam(name: 'UPDATE_DOCS', value: false), string(name: 'URL_SUBFOLDER', value: 'speedwagon')], wait: false
        }
    }
}

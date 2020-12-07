def AWS_PATH = "/usr/bin/aws"

properties([
    parameters([
        string(
            name: 'ENV',
            defaultValue: 'dev',
            description: 'Enter Environment'
        ),
        string(
            name: 'AZ',
            defaultValue: '2a',
            description: 'Enter AZ e.g. 2a/2b/2c'
        ),
        string(
            name: 'Monitoring',
            defaultValue: 'true',
            description: 'Enable Monitoring'
        ),
        string(
            name: 'EIP',
            defaultValue: '',
            description: 'Enter EIP'
        )
    ])
])

def TEMPLATEFILE="cleo-cicd/create_cleo_instance.templates"
def ENV="${ENV}"
def AZ="${AZ}"
def Monitoring="${Monitoring}"
def EIP="${EIP}"
def PARMFILE="cleo-cicd/${ENV}.parameters"
def STACK_NAME_REF = JOB_NAME.replace('/', '-')
def STACK_NAME="${STACK_NAME_REF}-${ENV}"
def check_stack
def create_stack

node {
    stage('Clonning the Repo'){
        sh 'date'
        echo STACK_NAME
        git master: 'master', credentialsId: 'gitlab_user_password', url: 'https://gitlab.com/clement_ayuk/CLEO.git'
    }

    stage('updating parameters'){
        sh "sed -i 's+AZ_SELECT+${AZ}+g' ${PARMFILE}"
        sh "sed -i 's+Monitoring_SELECT+${Monitoring}+g' ${PARMFILE}"
        sh "sed -i 's+ENV_SELECT+${ENV}+g' ${PARMFILE}"
        sh "sed -i 's+EIP_SELECT+${EIP}+g' ${PARMFILE}"
    }
   
    stage('Checking if Stack was Created') {
        check_stack = sh (
                script: "${AWS_PATH} cloudformation describe-stacks --profile default --stack-name ${STACK_NAME} --query 'Stacks[].StackStatus[]' --output text",
                returnStatus: true
                ) == 255
            echo "CFT status: ${check_stack}"
    }
        
    stage('Creating/Updating CFT Stack') {
        if ("${check_stack}" == "true") {
            create_stack = sh (
                script: "${AWS_PATH} cloudformation create-stack --profile default --stack-name ${STACK_NAME} --disable-rollback --capabilities CAPABILITY_IAM --template-body file://${WORKSPACE}/${TEMPLATEFILE} --parameters file://${WORKSPACE}/${PARMFILE}",
                returnStatus: true
                ) == 0
            echo "CFT Stack to create: ${create_stack}"
            if ("${create_stack}" == "true") {
                echo "${STACK_NAME} CFT Stack creation in progress"
            }
            else {
                echo "CFT Stack creation has problem, please check"
            }
        }
        else if ("${check_stack}" == "false") {
            echo "CFT Already created.. trying to update"
            check_created_stack_status = sh (
                script: "$AWS_PATH cloudformation describe-stacks --profile default --stack-name ${STACK_NAME} --query 'Stacks[].StackStatus[]' --output text",
                returnStdout: true
                ).trim()
            if ("${check_created_stack_status}" == "CREATE_COMPLETE" || "${check_created_stack_status}" == "UPDATE_COMPLETE") {
                update_stack = sh (
                script: "${AWS_PATH} cloudformation update-stack --profile default --stack-name ${STACK_NAME} --capabilities CAPABILITY_IAM --template-body file://${WORKSPACE}/${TEMPLATEFILE} --parameters file://${WORKSPACE}/${PARMFILE}",
                returnStatus: true
                ) == 0
                if ("${update_stack}" == "true") {
                    echo "${STACK_NAME} CFT is in update in progress"
                }
                else {
                    echo "CFT Stack has no modification OR updation has some problem, please check"
                }
            }
        }
        else {
            echo 'some thing going wrong, please check'
        }
    }
    stage('Monitoring the CFT Status') {
        cftstatus = 'CREATE_IN_PROGRESS'
        while( "${cftstatus}" == "CREATE_IN_PROGRESS" || "${cftstatus}" == "UPDATE_IN_PROGRESS" ){
            cftstatus = sh (
            script: "${AWS_PATH} cloudformation describe-stacks --profile default --stack-name ${STACK_NAME} --query 'Stacks[].StackStatus[]' --output text",
            returnStdout: true
            ).trim()
            echo "Status - ${cftstatus}"
            sleep(5)
        }
    }
}

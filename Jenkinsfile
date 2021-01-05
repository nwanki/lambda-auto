def AWS_PATH = "/usr/bin/aws"
def TEMPLATEFILE="create_lambda_cft.templates"
def PARMFILE="create_lambda_cft.parameters"
def STACK_NAME_REF = JOB_NAME.replace('/', '-')
def STACK_NAME_REF_1 = STACK_NAME_REF.replace('_', '-')
def STACK_NAME="${STACK_NAME_REF_1}-${ENV}"
def ZIP_FILE_NAME="${BUILD_TAG}"
def check_stack
def create_stack
def ROLE_ARN="${ROLE_ARN}"
def S3_BUCKET_NAME="${S3_BUCKET_NAME}"
def EXECUTABLE="${EXECUTABLE}"
def LAMBDA_TIMEOUT="${LAMBDA_TIMEOUT}"

node {
    stage('Clonning the Repo'){
        sh 'date'
        echo STACK_NAME
        git branch: 'main', credentialsId: 'github_neba', url: 'https://github.com/nwanki/lambda-auto.git'
    }

    stage('updating parameters'){
        sh "sed -i 's+ROLE_SELECT+${ROLE_ARN}+g' ${PARMFILE}"
        sh "sed -i 's+S3_BUCKET_NAME_SELECT+${S3_BUCKET_NAME}+g' ${PARMFILE}"
        sh "sed -i 's+CODE_ZIP_SELECT+${ZIP_FILE_NAME}.zip+g' ${PARMFILE}"
        sh "sed -i 's+RUNTIME_SELECT+${EXECUTABLE}+g' ${PARMFILE}"
        sh "sed -i 's+TIME_OUT_SELECT+${LAMBDA_TIMEOUT}+g' ${PARMFILE}"
    }
    
    stage('Creating Code ZIP file'){
        sh "zip -g ${ZIP_FILE_NAME}.zip lambda_function.py"
    }
    stage('Uploading ZIP file to S3 Bucket'){
        sh "${AWS_PATH} s3 cp ${ZIP_FILE_NAME}.zip s3://${S3_BUCKET_NAME}/${ZIP_FILE_NAME}.zip"
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

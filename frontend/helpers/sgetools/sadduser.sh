#!/bin/bash

# setup default variables
USER_TEMPLATE="user.template"
PROJECT_TEMPLATE="project.template"
ACL_TEMPLATE="acl.template"

if [ -z "$SGE_ARCH" ]; then
    SGE_ARCH=`$SGE_ROOT/util/arch`;
fi

QCONF="$SGE_ROOT/bin/$SGE_ARCH/qconf"
SGE_ADMIN_LOG="SGEAdmin.log"

if [ $# -lt 2 ]; then
    echo "$0: Usage $0 <userName> <projectName> [<departmentName>]"
    exit -1
fi

if [ ! -r $ACL_TEMPLATE ]; then
    echo "$0: Cannot find ACL template file '$ACL_TEMPLATE'. Put it in current directory or modify variable ACL_TEMPLATE in this script."
    exit -1
fi

if [ ! -r $PROJECT_TEMPLATE ]; then
    echo "$0: Cannot find project template file '$PROJECT_TEMPLATE'. Put it in current directory or modify variable PROJECT_TEMPLATE in this script."
    exit -1
fi

if [ ! -r $ACL_TEMPLATE ]; then
    echo "$0: Cannot find user template file '$USER_TEMPLATE'. Put it in current directory or modify variable USER_TEMPLATE in this script."
    exit -1
fi


echo "INFO: Begin adding user $1 / project $2" >> $SGE_ADMIN_LOG


acl_exists=`$QCONF -su $2 2>&1 | grep 'does not exist'`
if [ -n "$acl_exists" ]; then
    # create ACL with the same name as project
    echo "INFO: Creating new ACL $2"
    cp -f $ACL_TEMPLATE $ACL_TEMPLATE.$2
    sed -i s/"<project>"/$2/ $ACL_TEMPLATE.$2
    $QCONF -Au $ACL_TEMPLATE.$2 >> $SGE_ADMIN_LOG 2>&1
    rm -f $ACL_TEMPLATE.$2
else
    echo "INFO: ACL $2 already exists"
fi


project_exists=`$QCONF -sprj $2 2>&1 | grep 'is not known'`
if [ -n "$project_exists" ]; then
    # create new project
    echo "INFO: Creating new project $2"
    cp -f $PROJECT_TEMPLATE $PROJECT_TEMPLATE.$2
    sed -i s/"<project>"/$2/ $PROJECT_TEMPLATE.$2
    $QCONF -Aprj $PROJECT_TEMPLATE.$2 >> $SGE_ADMIN_LOG 2>&1
    rm -f $PROJECT_TEMPLATE.$2

    # create node in share three for the project
    $QCONF -astnode /$2=1 >> $SGE_ADMIN_LOG 2>&1
else
    echo "INFO: Project $2 already exists"
fi

user_exists=`$QCONF -suser $1 2>&1 | grep 'is not known'`
if [ -n "$user_exists" ]; then
    # create new user 
    echo "INFO: Creating new user $1"
    cp -f $USER_TEMPLATE $USER_TEMPLATE.$1
    sed -i s/"<user>"/$1/ $USER_TEMPLATE.$1 
    sed -i s/"<project>"/$2/ $USER_TEMPLATE.$1
    $QCONF -Auser $USER_TEMPLATE.$1 >> $SGE_ADMIN_LOG 2>&1
    rm -f $USER_TEMPLATE.$1
else
    echo "INFO: User $1 already exists, modifying it"
    cp -f $USER_TEMPLATE $USER_TEMPLATE.$1
    sed -i s/"<user>"/$1/ $USER_TEMPLATE.$1
    sed -i s/"<project>"/$2/ $USER_TEMPLATE.$1
    $QCONF -Muser $USER_TEMPLATE.$1 >> $SGE_ADMIN_LOG 2>&1
    rm -f $USER_TEMPLATE.$1
fi

#if [ -n "$user_exists" -o -n "$project_exists" ]; then
    # add user to ACL
    echo "INFO: Adding user $1 to ACL $2"
    $QCONF -au $1 $2 >> $SGE_ADMIN_LOG 2>&1

    # add user to project's tree
    echo "INFO: Adding user $1 to share tree"
    $QCONF -astnode /$2/$1=1 >> $SGE_ADMIN_LOG 2>&1
#fi
 
echo "INFO: End adding user $1 / project $2" >> $SGE_ADMIN_LOG

exit 0



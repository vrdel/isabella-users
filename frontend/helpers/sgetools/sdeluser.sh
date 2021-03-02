#!/bin/bash

if [ -z "$SGE_ARCH" ]; then
    SGE_ARCH=`$SGE_ROOT/util/arch`;
fi

QCONF="$SGE_ROOT/bin/$SGE_ARCH/qconf"
SGE_ADMIN_LOG="SGEAdmin.log"

echo "INFO: Begin removing user $1 / project $2" >> $SGE_ADMIN_LOG

# remove user from ACL
echo "INFO: Remove user $1 from ACL $2"
$QCONF -du $1 $2 >> $SGE_ADMIN_LOG 2>&1

# remove user from project's tree
echo "INFO: Remove user $1 from share tree"
$QCONF -dstnode /$2/$1 >> $SGE_ADMIN_LOG 2>&1

echo "INFO: End remove user $1 / project $2" >> $SGE_ADMIN_LOG

exit 0

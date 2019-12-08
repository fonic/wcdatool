#!/bin/bash

# -------------------------------------------------------------------------
#                                                                         -
#  Created by Fonic (https://github.com/fonic)                            -
#  Date: 06/16/19                                                         -
#                                                                         -
# -------------------------------------------------------------------------

dst_dir="open-watcom-v2"

if [[ -d "${dst_dir}" ]]; then
	rm -rf "${dst_dir}.old" && mv "${dst_dir}" "${dst_dir}.old" || exit $?
fi

git clone --depth=1 https://github.com/open-watcom/open-watcom-v2.git "${dst_dir}"
exit $?

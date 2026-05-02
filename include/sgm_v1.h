/**
 * SGM v1 gesture bytecode — wire constants.
 *
 * Must stay aligned with `src/gest/sgm_constants.py` (same numeric values).
 */
#ifndef GEST_SGM_V1_H
#define GEST_SGM_V1_H

#include <stdint.h>

/** Magic bytes on wire: 'S','G','M', 0x01 */
#define SGM_V1_MAGIC0 0x53u
#define SGM_V1_MAGIC1 0x47u
#define SGM_V1_MAGIC2 0x4Du
#define SGM_V1_MAGIC3 0x01u

#define SGM_V1_FORMAT_VERSION 1u

#define SGM_V1_KIND_ARTICULATED 1u
#define SGM_V1_KIND_DIRECTION   2u

#define SGM_V1_OP_FRAME       0x30u
#define SGM_V1_OP_JOINTS_F32  0x31u
#define SGM_V1_OP_STATE       0x32u
#define SGM_V1_OP_DIR_F32     0x33u
#define SGM_V1_OP_END         0xFFu

#endif /* GEST_SGM_V1_H */

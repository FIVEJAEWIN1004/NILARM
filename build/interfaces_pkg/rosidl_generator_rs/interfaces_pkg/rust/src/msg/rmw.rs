#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__msg__FruitDetection() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__msg__FruitDetection__init(msg: *mut FruitDetection) -> bool;
    fn interfaces_pkg__msg__FruitDetection__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<FruitDetection>, size: usize) -> bool;
    fn interfaces_pkg__msg__FruitDetection__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<FruitDetection>);
    fn interfaces_pkg__msg__FruitDetection__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<FruitDetection>, out_seq: *mut rosidl_runtime_rs::Sequence<FruitDetection>) -> bool;
}

// Corresponds to interfaces_pkg__msg__FruitDetection
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FruitDetection {
    /// 카메라/팔 기준 상대좌표 (m)
    pub x: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub z: f32,

    /// "ripe"(익음) 또는 "bad"(불량)
    pub quality: rosidl_runtime_rs::String,

    /// 탐지 신뢰도 0.0~1.0
    pub confidence: f32,

}



impl Default for FruitDetection {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__msg__FruitDetection__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__msg__FruitDetection__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for FruitDetection {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__FruitDetection__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__FruitDetection__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__FruitDetection__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for FruitDetection {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for FruitDetection where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/msg/FruitDetection";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__msg__FruitDetection() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__msg__BasketStatus() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__msg__BasketStatus__init(msg: *mut BasketStatus) -> bool;
    fn interfaces_pkg__msg__BasketStatus__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<BasketStatus>, size: usize) -> bool;
    fn interfaces_pkg__msg__BasketStatus__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<BasketStatus>);
    fn interfaces_pkg__msg__BasketStatus__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<BasketStatus>, out_seq: *mut rosidl_runtime_rs::Sequence<BasketStatus>) -> bool;
}

// Corresponds to interfaces_pkg__msg__BasketStatus
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct BasketStatus {
    /// 현재 적재된 개수
    pub weight: i32,

    /// 소형바구니 최대 용량
    pub maxweight: i32,

    /// count >= capacity 여부
    pub is_full: bool,

}



impl Default for BasketStatus {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__msg__BasketStatus__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__msg__BasketStatus__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for BasketStatus {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__BasketStatus__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__BasketStatus__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__BasketStatus__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for BasketStatus {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for BasketStatus where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/msg/BasketStatus";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__msg__BasketStatus() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__msg__MissionState() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__msg__MissionState__init(msg: *mut MissionState) -> bool;
    fn interfaces_pkg__msg__MissionState__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<MissionState>, size: usize) -> bool;
    fn interfaces_pkg__msg__MissionState__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<MissionState>);
    fn interfaces_pkg__msg__MissionState__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<MissionState>, out_seq: *mut rosidl_runtime_rs::Sequence<MissionState>) -> bool;
}

// Corresponds to interfaces_pkg__msg__MissionState
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct MissionState {
    /// "IDLE","NAV_TO_LOADING","HARVEST","DUMP","CHECK_GOAL","NAV_TO_UNLOAD","COMPLETE","ERROR"
    pub state: rosidl_runtime_rs::String,

    /// 지금까지 누적 수확 개수
    pub harvested_total: i32,

    /// 목표 수확 개수
    pub goal_count: i32,

}



impl Default for MissionState {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__msg__MissionState__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__msg__MissionState__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for MissionState {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__MissionState__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__MissionState__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__MissionState__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for MissionState {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for MissionState where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/msg/MissionState";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__msg__MissionState() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__msg__LaneCenter() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__msg__LaneCenter__init(msg: *mut LaneCenter) -> bool;
    fn interfaces_pkg__msg__LaneCenter__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<LaneCenter>, size: usize) -> bool;
    fn interfaces_pkg__msg__LaneCenter__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<LaneCenter>);
    fn interfaces_pkg__msg__LaneCenter__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<LaneCenter>, out_seq: *mut rosidl_runtime_rs::Sequence<LaneCenter>) -> bool;
}

// Corresponds to interfaces_pkg__msg__LaneCenter
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct LaneCenter {

    // This member is not documented.
    #[allow(missing_docs)]
    pub center_x: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub image_center_x: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub error: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub confidence: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub detected: bool,

}



impl Default for LaneCenter {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__msg__LaneCenter__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__msg__LaneCenter__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for LaneCenter {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__LaneCenter__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__LaneCenter__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__LaneCenter__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for LaneCenter {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for LaneCenter where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/msg/LaneCenter";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__msg__LaneCenter() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__msg__RoadModel() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__msg__RoadModel__init(msg: *mut RoadModel) -> bool;
    fn interfaces_pkg__msg__RoadModel__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<RoadModel>, size: usize) -> bool;
    fn interfaces_pkg__msg__RoadModel__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<RoadModel>);
    fn interfaces_pkg__msg__RoadModel__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<RoadModel>, out_seq: *mut rosidl_runtime_rs::Sequence<RoadModel>) -> bool;
}

// Corresponds to interfaces_pkg__msg__RoadModel
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct RoadModel {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub left_detected: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub right_detected: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub center_valid: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub predicted: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub left_x: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub right_x: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub center_x: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub image_center_x: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub lane_width_px: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub lateral_error_px: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub heading_error_rad: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub curvature: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub confidence: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub branch_flags: u8,

}

impl RoadModel {

    // This constant is not documented.
    #[allow(missing_docs)]
    pub const BRANCH_NONE: u8 = 0;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const BRANCH_EXTRA_BOUNDARY: u8 = 1;

}


impl Default for RoadModel {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__msg__RoadModel__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__msg__RoadModel__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for RoadModel {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__RoadModel__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__RoadModel__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__RoadModel__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for RoadModel {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for RoadModel where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/msg/RoadModel";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__msg__RoadModel() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__msg__ObstacleStatus() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__msg__ObstacleStatus__init(msg: *mut ObstacleStatus) -> bool;
    fn interfaces_pkg__msg__ObstacleStatus__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ObstacleStatus>, size: usize) -> bool;
    fn interfaces_pkg__msg__ObstacleStatus__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ObstacleStatus>);
    fn interfaces_pkg__msg__ObstacleStatus__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ObstacleStatus>, out_seq: *mut rosidl_runtime_rs::Sequence<ObstacleStatus>) -> bool;
}

// Corresponds to interfaces_pkg__msg__ObstacleStatus
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ObstacleStatus {

    // This member is not documented.
    #[allow(missing_docs)]
    pub front_distance: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub left_distance: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub right_distance: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub obstacle_detected: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub emergency_stop: bool,

}



impl Default for ObstacleStatus {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__msg__ObstacleStatus__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__msg__ObstacleStatus__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ObstacleStatus {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__ObstacleStatus__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__ObstacleStatus__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__msg__ObstacleStatus__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ObstacleStatus {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ObstacleStatus where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/msg/ObstacleStatus";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__msg__ObstacleStatus() }
  }
}



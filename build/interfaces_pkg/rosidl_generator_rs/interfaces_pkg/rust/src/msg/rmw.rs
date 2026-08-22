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



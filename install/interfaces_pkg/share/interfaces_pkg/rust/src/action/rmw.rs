
#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_Goal() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__Harvest_Goal__init(msg: *mut Harvest_Goal) -> bool;
    fn interfaces_pkg__action__Harvest_Goal__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Harvest_Goal>, size: usize) -> bool;
    fn interfaces_pkg__action__Harvest_Goal__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Harvest_Goal>);
    fn interfaces_pkg__action__Harvest_Goal__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Harvest_Goal>, out_seq: *mut rosidl_runtime_rs::Sequence<Harvest_Goal>) -> bool;
}

// Corresponds to interfaces_pkg__action__Harvest_Goal
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Harvest_Goal {
    /// 이번에 몇 개 수확할지 목표 !git
    pub target_count: i32,

}



impl Default for Harvest_Goal {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__Harvest_Goal__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__Harvest_Goal__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Harvest_Goal {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_Goal__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_Goal__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_Goal__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Harvest_Goal {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Harvest_Goal where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/Harvest_Goal";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_Goal() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_Result() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__Harvest_Result__init(msg: *mut Harvest_Result) -> bool;
    fn interfaces_pkg__action__Harvest_Result__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Harvest_Result>, size: usize) -> bool;
    fn interfaces_pkg__action__Harvest_Result__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Harvest_Result>);
    fn interfaces_pkg__action__Harvest_Result__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Harvest_Result>, out_seq: *mut rosidl_runtime_rs::Sequence<Harvest_Result>) -> bool;
}

// Corresponds to interfaces_pkg__action__Harvest_Result
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Harvest_Result {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,

    /// 실제로 수확한 개수
    pub harvested_count: i32,

}



impl Default for Harvest_Result {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__Harvest_Result__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__Harvest_Result__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Harvest_Result {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_Result__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_Result__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_Result__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Harvest_Result {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Harvest_Result where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/Harvest_Result";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_Result() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_Feedback() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__Harvest_Feedback__init(msg: *mut Harvest_Feedback) -> bool;
    fn interfaces_pkg__action__Harvest_Feedback__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Harvest_Feedback>, size: usize) -> bool;
    fn interfaces_pkg__action__Harvest_Feedback__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Harvest_Feedback>);
    fn interfaces_pkg__action__Harvest_Feedback__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Harvest_Feedback>, out_seq: *mut rosidl_runtime_rs::Sequence<Harvest_Feedback>) -> bool;
}

// Corresponds to interfaces_pkg__action__Harvest_Feedback
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Harvest_Feedback {
    /// 지금까지 몇 개 땄는지 !!
    pub current_count: i32,

    /// "searching", "grasping", "placing" 등
    pub status: rosidl_runtime_rs::String,

}



impl Default for Harvest_Feedback {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__Harvest_Feedback__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__Harvest_Feedback__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Harvest_Feedback {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_Feedback__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_Feedback__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_Feedback__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Harvest_Feedback {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Harvest_Feedback where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/Harvest_Feedback";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_Feedback() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_FeedbackMessage() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__Harvest_FeedbackMessage__init(msg: *mut Harvest_FeedbackMessage) -> bool;
    fn interfaces_pkg__action__Harvest_FeedbackMessage__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Harvest_FeedbackMessage>, size: usize) -> bool;
    fn interfaces_pkg__action__Harvest_FeedbackMessage__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Harvest_FeedbackMessage>);
    fn interfaces_pkg__action__Harvest_FeedbackMessage__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Harvest_FeedbackMessage>, out_seq: *mut rosidl_runtime_rs::Sequence<Harvest_FeedbackMessage>) -> bool;
}

// Corresponds to interfaces_pkg__action__Harvest_FeedbackMessage
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Harvest_FeedbackMessage {

    // This member is not documented.
    #[allow(missing_docs)]
    pub goal_id: unique_identifier_msgs::msg::rmw::UUID,


    // This member is not documented.
    #[allow(missing_docs)]
    pub feedback: super::super::action::rmw::Harvest_Feedback,

}



impl Default for Harvest_FeedbackMessage {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__Harvest_FeedbackMessage__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__Harvest_FeedbackMessage__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Harvest_FeedbackMessage {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_FeedbackMessage__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_FeedbackMessage__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_FeedbackMessage__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Harvest_FeedbackMessage {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Harvest_FeedbackMessage where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/Harvest_FeedbackMessage";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_FeedbackMessage() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_Goal() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__DumpBasket_Goal__init(msg: *mut DumpBasket_Goal) -> bool;
    fn interfaces_pkg__action__DumpBasket_Goal__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_Goal>, size: usize) -> bool;
    fn interfaces_pkg__action__DumpBasket_Goal__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_Goal>);
    fn interfaces_pkg__action__DumpBasket_Goal__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DumpBasket_Goal>, out_seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_Goal>) -> bool;
}

// Corresponds to interfaces_pkg__action__DumpBasket_Goal
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DumpBasket_Goal {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for DumpBasket_Goal {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__DumpBasket_Goal__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__DumpBasket_Goal__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DumpBasket_Goal {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_Goal__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_Goal__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_Goal__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DumpBasket_Goal {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DumpBasket_Goal where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/DumpBasket_Goal";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_Goal() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_Result() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__DumpBasket_Result__init(msg: *mut DumpBasket_Result) -> bool;
    fn interfaces_pkg__action__DumpBasket_Result__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_Result>, size: usize) -> bool;
    fn interfaces_pkg__action__DumpBasket_Result__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_Result>);
    fn interfaces_pkg__action__DumpBasket_Result__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DumpBasket_Result>, out_seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_Result>) -> bool;
}

// Corresponds to interfaces_pkg__action__DumpBasket_Result
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DumpBasket_Result {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub duration_sec: f32,

}



impl Default for DumpBasket_Result {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__DumpBasket_Result__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__DumpBasket_Result__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DumpBasket_Result {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_Result__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_Result__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_Result__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DumpBasket_Result {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DumpBasket_Result where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/DumpBasket_Result";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_Result() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_Feedback() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__DumpBasket_Feedback__init(msg: *mut DumpBasket_Feedback) -> bool;
    fn interfaces_pkg__action__DumpBasket_Feedback__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_Feedback>, size: usize) -> bool;
    fn interfaces_pkg__action__DumpBasket_Feedback__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_Feedback>);
    fn interfaces_pkg__action__DumpBasket_Feedback__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DumpBasket_Feedback>, out_seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_Feedback>) -> bool;
}

// Corresponds to interfaces_pkg__action__DumpBasket_Feedback
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DumpBasket_Feedback {
    /// "tilting", "pouring", "returning"
    pub phase: rosidl_runtime_rs::String,

}



impl Default for DumpBasket_Feedback {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__DumpBasket_Feedback__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__DumpBasket_Feedback__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DumpBasket_Feedback {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_Feedback__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_Feedback__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_Feedback__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DumpBasket_Feedback {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DumpBasket_Feedback where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/DumpBasket_Feedback";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_Feedback() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_FeedbackMessage() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__DumpBasket_FeedbackMessage__init(msg: *mut DumpBasket_FeedbackMessage) -> bool;
    fn interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_FeedbackMessage>, size: usize) -> bool;
    fn interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_FeedbackMessage>);
    fn interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DumpBasket_FeedbackMessage>, out_seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_FeedbackMessage>) -> bool;
}

// Corresponds to interfaces_pkg__action__DumpBasket_FeedbackMessage
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DumpBasket_FeedbackMessage {

    // This member is not documented.
    #[allow(missing_docs)]
    pub goal_id: unique_identifier_msgs::msg::rmw::UUID,


    // This member is not documented.
    #[allow(missing_docs)]
    pub feedback: super::super::action::rmw::DumpBasket_Feedback,

}



impl Default for DumpBasket_FeedbackMessage {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__DumpBasket_FeedbackMessage__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__DumpBasket_FeedbackMessage__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DumpBasket_FeedbackMessage {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DumpBasket_FeedbackMessage {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DumpBasket_FeedbackMessage where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/DumpBasket_FeedbackMessage";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_FeedbackMessage() }
  }
}




#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_SendGoal_Request() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__Harvest_SendGoal_Request__init(msg: *mut Harvest_SendGoal_Request) -> bool;
    fn interfaces_pkg__action__Harvest_SendGoal_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Harvest_SendGoal_Request>, size: usize) -> bool;
    fn interfaces_pkg__action__Harvest_SendGoal_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Harvest_SendGoal_Request>);
    fn interfaces_pkg__action__Harvest_SendGoal_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Harvest_SendGoal_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<Harvest_SendGoal_Request>) -> bool;
}

// Corresponds to interfaces_pkg__action__Harvest_SendGoal_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Harvest_SendGoal_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub goal_id: unique_identifier_msgs::msg::rmw::UUID,


    // This member is not documented.
    #[allow(missing_docs)]
    pub goal: super::super::action::rmw::Harvest_Goal,

}



impl Default for Harvest_SendGoal_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__Harvest_SendGoal_Request__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__Harvest_SendGoal_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Harvest_SendGoal_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_SendGoal_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_SendGoal_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_SendGoal_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Harvest_SendGoal_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Harvest_SendGoal_Request where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/Harvest_SendGoal_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_SendGoal_Request() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_SendGoal_Response() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__Harvest_SendGoal_Response__init(msg: *mut Harvest_SendGoal_Response) -> bool;
    fn interfaces_pkg__action__Harvest_SendGoal_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Harvest_SendGoal_Response>, size: usize) -> bool;
    fn interfaces_pkg__action__Harvest_SendGoal_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Harvest_SendGoal_Response>);
    fn interfaces_pkg__action__Harvest_SendGoal_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Harvest_SendGoal_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<Harvest_SendGoal_Response>) -> bool;
}

// Corresponds to interfaces_pkg__action__Harvest_SendGoal_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Harvest_SendGoal_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub accepted: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub stamp: builtin_interfaces::msg::rmw::Time,

}



impl Default for Harvest_SendGoal_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__Harvest_SendGoal_Response__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__Harvest_SendGoal_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Harvest_SendGoal_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_SendGoal_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_SendGoal_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_SendGoal_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Harvest_SendGoal_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Harvest_SendGoal_Response where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/Harvest_SendGoal_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_SendGoal_Response() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_GetResult_Request() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__Harvest_GetResult_Request__init(msg: *mut Harvest_GetResult_Request) -> bool;
    fn interfaces_pkg__action__Harvest_GetResult_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Harvest_GetResult_Request>, size: usize) -> bool;
    fn interfaces_pkg__action__Harvest_GetResult_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Harvest_GetResult_Request>);
    fn interfaces_pkg__action__Harvest_GetResult_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Harvest_GetResult_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<Harvest_GetResult_Request>) -> bool;
}

// Corresponds to interfaces_pkg__action__Harvest_GetResult_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Harvest_GetResult_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub goal_id: unique_identifier_msgs::msg::rmw::UUID,

}



impl Default for Harvest_GetResult_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__Harvest_GetResult_Request__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__Harvest_GetResult_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Harvest_GetResult_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_GetResult_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_GetResult_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_GetResult_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Harvest_GetResult_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Harvest_GetResult_Request where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/Harvest_GetResult_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_GetResult_Request() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_GetResult_Response() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__Harvest_GetResult_Response__init(msg: *mut Harvest_GetResult_Response) -> bool;
    fn interfaces_pkg__action__Harvest_GetResult_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Harvest_GetResult_Response>, size: usize) -> bool;
    fn interfaces_pkg__action__Harvest_GetResult_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Harvest_GetResult_Response>);
    fn interfaces_pkg__action__Harvest_GetResult_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Harvest_GetResult_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<Harvest_GetResult_Response>) -> bool;
}

// Corresponds to interfaces_pkg__action__Harvest_GetResult_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Harvest_GetResult_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub status: i8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub result: super::super::action::rmw::Harvest_Result,

}



impl Default for Harvest_GetResult_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__Harvest_GetResult_Response__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__Harvest_GetResult_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Harvest_GetResult_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_GetResult_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_GetResult_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__Harvest_GetResult_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Harvest_GetResult_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Harvest_GetResult_Response where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/Harvest_GetResult_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__Harvest_GetResult_Response() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_SendGoal_Request() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__DumpBasket_SendGoal_Request__init(msg: *mut DumpBasket_SendGoal_Request) -> bool;
    fn interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_SendGoal_Request>, size: usize) -> bool;
    fn interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_SendGoal_Request>);
    fn interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DumpBasket_SendGoal_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_SendGoal_Request>) -> bool;
}

// Corresponds to interfaces_pkg__action__DumpBasket_SendGoal_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DumpBasket_SendGoal_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub goal_id: unique_identifier_msgs::msg::rmw::UUID,


    // This member is not documented.
    #[allow(missing_docs)]
    pub goal: super::super::action::rmw::DumpBasket_Goal,

}



impl Default for DumpBasket_SendGoal_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__DumpBasket_SendGoal_Request__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__DumpBasket_SendGoal_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DumpBasket_SendGoal_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DumpBasket_SendGoal_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DumpBasket_SendGoal_Request where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/DumpBasket_SendGoal_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_SendGoal_Request() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_SendGoal_Response() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__DumpBasket_SendGoal_Response__init(msg: *mut DumpBasket_SendGoal_Response) -> bool;
    fn interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_SendGoal_Response>, size: usize) -> bool;
    fn interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_SendGoal_Response>);
    fn interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DumpBasket_SendGoal_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_SendGoal_Response>) -> bool;
}

// Corresponds to interfaces_pkg__action__DumpBasket_SendGoal_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DumpBasket_SendGoal_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub accepted: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub stamp: builtin_interfaces::msg::rmw::Time,

}



impl Default for DumpBasket_SendGoal_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__DumpBasket_SendGoal_Response__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__DumpBasket_SendGoal_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DumpBasket_SendGoal_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DumpBasket_SendGoal_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DumpBasket_SendGoal_Response where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/DumpBasket_SendGoal_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_SendGoal_Response() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_GetResult_Request() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__DumpBasket_GetResult_Request__init(msg: *mut DumpBasket_GetResult_Request) -> bool;
    fn interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_GetResult_Request>, size: usize) -> bool;
    fn interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_GetResult_Request>);
    fn interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DumpBasket_GetResult_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_GetResult_Request>) -> bool;
}

// Corresponds to interfaces_pkg__action__DumpBasket_GetResult_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DumpBasket_GetResult_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub goal_id: unique_identifier_msgs::msg::rmw::UUID,

}



impl Default for DumpBasket_GetResult_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__DumpBasket_GetResult_Request__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__DumpBasket_GetResult_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DumpBasket_GetResult_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DumpBasket_GetResult_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DumpBasket_GetResult_Request where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/DumpBasket_GetResult_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_GetResult_Request() }
  }
}


#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_GetResult_Response() -> *const std::ffi::c_void;
}

#[link(name = "interfaces_pkg__rosidl_generator_c")]
extern "C" {
    fn interfaces_pkg__action__DumpBasket_GetResult_Response__init(msg: *mut DumpBasket_GetResult_Response) -> bool;
    fn interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_GetResult_Response>, size: usize) -> bool;
    fn interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_GetResult_Response>);
    fn interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DumpBasket_GetResult_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<DumpBasket_GetResult_Response>) -> bool;
}

// Corresponds to interfaces_pkg__action__DumpBasket_GetResult_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DumpBasket_GetResult_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub status: i8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub result: super::super::action::rmw::DumpBasket_Result,

}



impl Default for DumpBasket_GetResult_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces_pkg__action__DumpBasket_GetResult_Response__init(&mut msg as *mut _) {
        panic!("Call to interfaces_pkg__action__DumpBasket_GetResult_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DumpBasket_GetResult_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DumpBasket_GetResult_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DumpBasket_GetResult_Response where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces_pkg/action/DumpBasket_GetResult_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces_pkg__action__DumpBasket_GetResult_Response() }
  }
}






#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__interfaces_pkg__action__Harvest_SendGoal() -> *const std::ffi::c_void;
}

// Corresponds to interfaces_pkg__action__Harvest_SendGoal
#[allow(missing_docs, non_camel_case_types)]
pub struct Harvest_SendGoal;

impl rosidl_runtime_rs::Service for Harvest_SendGoal {
    type Request = Harvest_SendGoal_Request;
    type Response = Harvest_SendGoal_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__interfaces_pkg__action__Harvest_SendGoal() }
    }
}




#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__interfaces_pkg__action__Harvest_GetResult() -> *const std::ffi::c_void;
}

// Corresponds to interfaces_pkg__action__Harvest_GetResult
#[allow(missing_docs, non_camel_case_types)]
pub struct Harvest_GetResult;

impl rosidl_runtime_rs::Service for Harvest_GetResult {
    type Request = Harvest_GetResult_Request;
    type Response = Harvest_GetResult_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__interfaces_pkg__action__Harvest_GetResult() }
    }
}




#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__interfaces_pkg__action__DumpBasket_SendGoal() -> *const std::ffi::c_void;
}

// Corresponds to interfaces_pkg__action__DumpBasket_SendGoal
#[allow(missing_docs, non_camel_case_types)]
pub struct DumpBasket_SendGoal;

impl rosidl_runtime_rs::Service for DumpBasket_SendGoal {
    type Request = DumpBasket_SendGoal_Request;
    type Response = DumpBasket_SendGoal_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__interfaces_pkg__action__DumpBasket_SendGoal() }
    }
}




#[link(name = "interfaces_pkg__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__interfaces_pkg__action__DumpBasket_GetResult() -> *const std::ffi::c_void;
}

// Corresponds to interfaces_pkg__action__DumpBasket_GetResult
#[allow(missing_docs, non_camel_case_types)]
pub struct DumpBasket_GetResult;

impl rosidl_runtime_rs::Service for DumpBasket_GetResult {
    type Request = DumpBasket_GetResult_Request;
    type Response = DumpBasket_GetResult_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__interfaces_pkg__action__DumpBasket_GetResult() }
    }
}



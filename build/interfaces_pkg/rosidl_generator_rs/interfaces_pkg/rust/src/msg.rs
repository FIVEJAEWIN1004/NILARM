#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to interfaces_pkg__msg__FruitDetection

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    pub quality: std::string::String,

    /// 탐지 신뢰도 0.0~1.0
    pub confidence: f32,

}



impl Default for FruitDetection {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::FruitDetection::default())
  }
}

impl rosidl_runtime_rs::Message for FruitDetection {
  type RmwMsg = super::msg::rmw::FruitDetection;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        x: msg.x,
        y: msg.y,
        z: msg.z,
        quality: msg.quality.as_str().into(),
        confidence: msg.confidence,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      x: msg.x,
      y: msg.y,
      z: msg.z,
        quality: msg.quality.as_str().into(),
      confidence: msg.confidence,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      x: msg.x,
      y: msg.y,
      z: msg.z,
      quality: msg.quality.to_string(),
      confidence: msg.confidence,
    }
  }
}


// Corresponds to interfaces_pkg__msg__BasketStatus

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::BasketStatus::default())
  }
}

impl rosidl_runtime_rs::Message for BasketStatus {
  type RmwMsg = super::msg::rmw::BasketStatus;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        weight: msg.weight,
        maxweight: msg.maxweight,
        is_full: msg.is_full,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      weight: msg.weight,
      maxweight: msg.maxweight,
      is_full: msg.is_full,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      weight: msg.weight,
      maxweight: msg.maxweight,
      is_full: msg.is_full,
    }
  }
}


// Corresponds to interfaces_pkg__msg__MissionState

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct MissionState {
    /// "IDLE","NAV_TO_LOADING","HARVEST","DUMP","CHECK_GOAL","NAV_TO_UNLOAD","COMPLETE","ERROR"
    pub state: std::string::String,

    /// 지금까지 누적 수확 개수
    pub harvested_total: i32,

    /// 목표 수확 개수
    pub goal_count: i32,

}



impl Default for MissionState {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::MissionState::default())
  }
}

impl rosidl_runtime_rs::Message for MissionState {
  type RmwMsg = super::msg::rmw::MissionState;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        state: msg.state.as_str().into(),
        harvested_total: msg.harvested_total,
        goal_count: msg.goal_count,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        state: msg.state.as_str().into(),
      harvested_total: msg.harvested_total,
      goal_count: msg.goal_count,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      state: msg.state.to_string(),
      harvested_total: msg.harvested_total,
      goal_count: msg.goal_count,
    }
  }
}


// Corresponds to interfaces_pkg__msg__LaneCenter

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::LaneCenter::default())
  }
}

impl rosidl_runtime_rs::Message for LaneCenter {
  type RmwMsg = super::msg::rmw::LaneCenter;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        center_x: msg.center_x,
        image_center_x: msg.image_center_x,
        error: msg.error,
        confidence: msg.confidence,
        detected: msg.detected,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      center_x: msg.center_x,
      image_center_x: msg.image_center_x,
      error: msg.error,
      confidence: msg.confidence,
      detected: msg.detected,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      center_x: msg.center_x,
      image_center_x: msg.image_center_x,
      error: msg.error,
      confidence: msg.confidence,
      detected: msg.detected,
    }
  }
}


// Corresponds to interfaces_pkg__msg__RoadModel

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct RoadModel {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::RoadModel::default())
  }
}

impl rosidl_runtime_rs::Message for RoadModel {
  type RmwMsg = super::msg::rmw::RoadModel;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        left_detected: msg.left_detected,
        right_detected: msg.right_detected,
        center_valid: msg.center_valid,
        predicted: msg.predicted,
        left_x: msg.left_x,
        right_x: msg.right_x,
        center_x: msg.center_x,
        image_center_x: msg.image_center_x,
        lane_width_px: msg.lane_width_px,
        lateral_error_px: msg.lateral_error_px,
        heading_error_rad: msg.heading_error_rad,
        curvature: msg.curvature,
        confidence: msg.confidence,
        branch_flags: msg.branch_flags,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
      left_detected: msg.left_detected,
      right_detected: msg.right_detected,
      center_valid: msg.center_valid,
      predicted: msg.predicted,
      left_x: msg.left_x,
      right_x: msg.right_x,
      center_x: msg.center_x,
      image_center_x: msg.image_center_x,
      lane_width_px: msg.lane_width_px,
      lateral_error_px: msg.lateral_error_px,
      heading_error_rad: msg.heading_error_rad,
      curvature: msg.curvature,
      confidence: msg.confidence,
      branch_flags: msg.branch_flags,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      left_detected: msg.left_detected,
      right_detected: msg.right_detected,
      center_valid: msg.center_valid,
      predicted: msg.predicted,
      left_x: msg.left_x,
      right_x: msg.right_x,
      center_x: msg.center_x,
      image_center_x: msg.image_center_x,
      lane_width_px: msg.lane_width_px,
      lateral_error_px: msg.lateral_error_px,
      heading_error_rad: msg.heading_error_rad,
      curvature: msg.curvature,
      confidence: msg.confidence,
      branch_flags: msg.branch_flags,
    }
  }
}


// Corresponds to interfaces_pkg__msg__ObstacleStatus

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::ObstacleStatus::default())
  }
}

impl rosidl_runtime_rs::Message for ObstacleStatus {
  type RmwMsg = super::msg::rmw::ObstacleStatus;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        front_distance: msg.front_distance,
        left_distance: msg.left_distance,
        right_distance: msg.right_distance,
        obstacle_detected: msg.obstacle_detected,
        emergency_stop: msg.emergency_stop,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      front_distance: msg.front_distance,
      left_distance: msg.left_distance,
      right_distance: msg.right_distance,
      obstacle_detected: msg.obstacle_detected,
      emergency_stop: msg.emergency_stop,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      front_distance: msg.front_distance,
      left_distance: msg.left_distance,
      right_distance: msg.right_distance,
      obstacle_detected: msg.obstacle_detected,
      emergency_stop: msg.emergency_stop,
    }
  }
}



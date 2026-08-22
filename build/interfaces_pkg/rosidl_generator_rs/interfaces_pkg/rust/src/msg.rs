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



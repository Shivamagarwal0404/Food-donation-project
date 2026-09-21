/**
 * FoodShare — TypeScript Types
 * Shared domain type definitions for the FoodShare platform.
 */

export type UserRole = 'admin' | 'donor' | 'ngo_receiver' | 'volunteer'

export interface DonorProfile {
  id: number
  donor_type: string
  organization_name: string
  fssai_license: string
  created_at: string
}

export interface NGOProfile {
  id: number
  organization_name: string
  registration_number: string
  mission_statement: string
  capacity_servings_per_day: number
  is_verified: boolean
  created_at: string
}

export interface VolunteerProfile {
  id: number
  vehicle_type: string
  is_available: boolean
  deliveries_completed: number
  created_at: string
}

export interface Address {
  id: number
  label: string
  contact_person: string
  contact_phone: string
  address_line1: string
  address_line2?: string
  city: string
  state: string
  pincode: string
  country: string
  is_default: boolean
  created_at: string
}

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  phone_number: string
  role: UserRole
  donor_profile?: DonorProfile
  ngo_profile?: NGOProfile
  volunteer_profile?: VolunteerProfile
  addresses?: Address[]
  created_at: string
}

export interface FoodCategory {
  id: number
  name: string
  slug: string
  description?: string
  icon?: string
  is_active?: boolean
}

export type DietaryType = 'VEG' | 'NON_VEG' | 'VEGAN' | 'EGG'
export type QuantityUnit = 'kg' | 'meals' | 'packets' | 'liters'

export type DonationStatus =
  | 'AVAILABLE'
  | 'REQUESTED'
  | 'ACCEPTED'
  | 'PICKUP_ASSIGNED'
  | 'PICKED_UP'
  | 'DELIVERED'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'EXPIRED'

export interface FoodDonation {
  id: number
  title: string
  description: string
  donor: number
  donor_details?: User
  category: number
  other_food_item?: string | null
  category_details?: FoodCategory
  dietary_type: DietaryType
  quantity: number
  unit: QuantityUnit
  servings: number
  prepared_at?: string
  expiry_at: string
  pickup_address: string
  pickup_city: string
  pickup_contact_phone: string
  image?: string
  status: DonationStatus
  status_display: string
  special_instructions?: string
  requests?: DonationRequest[]
  created_at: string
  updated_at: string
}

export interface DonationRequest {
  id: number
  donation: number
  donation_title?: string
  receiver: number
  receiver_details?: User
  requested_servings: number
  message: string
  status: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'CANCELLED'
  created_at: string
  updated_at: string
}

export type PickupStatus =
  | 'PENDING'
  | 'ASSIGNED'
  | 'PICKED_UP'
  | 'DELIVERED'
  | 'COMPLETED'
  | 'CANCELLED'

export interface Pickup {
  id: number
  donation: number
  donation_details?: FoodDonation
  volunteer?: number
  volunteer_details?: User
  pickup_location: string
  delivery_location?: string
  scheduled_time?: string
  status: PickupStatus
  status_display: string
  notes?: string
  picked_up_at?: string
  delivered_at?: string
  created_at: string
  updated_at: string
}

export interface ImpactMetrics {
  total_donations: number
  available_donations: number
  completed_donations: number
  cancelled_donations: number
  meals_rescued: number
  food_rescued_kg_estimate: number
  completion_rate_percentage: number
}

export interface CommunityMetrics {
  active_donors: number
  registered_ngos: number
  delivery_volunteers: number
}

export interface PlatformImpact {
  metrics: ImpactMetrics
  community: CommunityMetrics
  assumptions: {
    meals_calculation: string
    kg_calculation: string
  }
  recent_activity: Array<{
    id: number
    title: string
    donor_name: string
    city: string
    servings: number
    completed_at: string
  }>
}

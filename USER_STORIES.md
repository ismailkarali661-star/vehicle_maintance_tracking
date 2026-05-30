# User Stories & Acceptance Criteria
## Vehicle Maintenance Tracking App

---

## US1 — Araç Ekleme ve Yönetme
**As a** registered user,  
**I want to** add my vehicles to the system with details like brand, model, year, plate and fuel type,  
**So that** I can track each vehicle's maintenance history separately.

### Acceptance Criteria
- [ ] User can add a vehicle with brand, model, year, plate, fuel type, mileage, engine and color fields
- [ ] Plate number must be unique in the system — duplicate plates are rejected with an error message
- [ ] Year must be between 1900 and current year + 1
- [ ] Fuel type defaults to "benzin" if not selected
- [ ] User can edit any field of an existing vehicle
- [ ] User can delete a vehicle — all related maintenance and fault records are also deleted
- [ ] User can only see and manage their own vehicles, not other users' vehicles

---

## US2 — Bakım Kaydı Ekleme
**As a** vehicle owner,  
**I want to** record maintenance operations (oil change, tire rotation, etc.) for my vehicles,  
**So that** I can keep a complete service history and know when the next service is due.

### Acceptance Criteria
- [ ] User can add a maintenance record with type, date, mileage, cost and service provider
- [ ] Maintenance type and date are required fields — form is rejected without them
- [ ] User can optionally set next service mileage and next service date
- [ ] User can edit or delete any maintenance record
- [ ] Maintenance records are listed in reverse chronological order (newest first)
- [ ] Total maintenance cost is calculated and displayed per vehicle

---

## US3 — Arıza Takibi
**As a** vehicle owner,  
**I want to** log faults and problems with my vehicle,  
**So that** I can track unresolved issues and monitor repair costs.

### Acceptance Criteria
- [ ] User can add a fault with title, description, category, severity and date
- [ ] Fault categories include: motor, şanzıman, fren, elektrik, süspansiyon, diğer
- [ ] Severity levels are: low, medium, high
- [ ] Fault status is "open" by default and can be marked as "resolved"
- [ ] Resolved faults automatically record the resolution date
- [ ] Open fault count is displayed as a badge on the vehicle card in dashboard
- [ ] Repair costs from faults are included in the total cost calculation

---

## US4 — Bakım Danışmanı (Advisor)
**As a** vehicle owner,  
**I want to** see which maintenance operations are overdue or coming up soon for my vehicle,  
**So that** I can proactively service my vehicle before problems occur.

### Acceptance Criteria
- [ ] System compares vehicle's current mileage against maintenance templates
- [ ] Overdue items (past due mileage) are shown in red
- [ ] Items due within 1000 km are shown in orange
- [ ] Items due within 5000 km are shown in yellow
- [ ] Good/completed items are shown in green
- [ ] Estimated cost range is shown for overdue and upcoming items
- [ ] Oil change interval is adjusted based on engine size (small/medium/large)

---

## US5 — Araç Satın Alma Rehberi
**As a** user considering buying a used car,  
**I want to** look up a vehicle model and see its known chronic faults and maintenance schedule,  
**So that** I can make an informed purchase decision.

### Acceptance Criteria
- [ ] User can search by brand and model from a catalog of 100+ vehicles
- [ ] Known chronic faults are listed with severity, category and approximate mileage they appear
- [ ] A 200,000 km maintenance schedule is generated based on the vehicle's fuel type
- [ ] Buyer guide notes show pros, cons, overall score and target buyer profile
- [ ] Electric vehicles show a different maintenance schedule than petrol/diesel
- [ ] Results are shown only after brand and model are selected

---

## US6 — Dashboard ve Genel Özet
**As a** registered user,  
**I want to** see an overview of all my vehicles and their status when I log in,  
**So that** I can quickly identify which vehicles need attention.

### Acceptance Criteria
- [ ] Dashboard shows all vehicles owned by the logged-in user
- [ ] Overdue maintenance items across all vehicles are listed on the dashboard
- [ ] Upcoming maintenance (due soon) items are also highlighted
- [ ] Total cost per vehicle is displayed on vehicle cards
- [ ] Open fault count is shown per vehicle
- [ ] Dashboard is only accessible to logged-in users — others are redirected to login

---

## Kanban Board Columns

| Column | User Stories |
|--------|-------------|
| **To Do** | — |
| **In Progress** | — |
| **Done** | US1, US2, US3, US4, US5, US6 |

---

## Commit Reference Guide

| User Story | Feature | Example Commit |
|------------|---------|----------------|
| US1 | Vehicle CRUD | `[US1] vehicle add and delete completed` |
| US2 | Maintenance records | `[US2] maintenance record form added` |
| US3 | Fault tracking | `[US3] fault status update added` |
| US4 | Advisor analysis | `[US4] maintenance advisor analysis function` |
| US5 | Buyer guide | `[US5] buyer guide page added` |
| US6 | Dashboard | `[US6] dashboard overview implemented` |

# FinTrack - Enhanced Finance Dashboard

## Project Evolution
This project has been upgraded from a basic assignment into a polished, functional "Mandi-style" financial dashboard. It demonstrates a stronger understanding of UI/UX, RESTful API design, and Role-Based Access Control (RBAC) implementation while maintaining clean, readable codebase.

## Key Enhancements
*   **Modern Sidebar Layout:** Implemented a persistent sidebar with navigation (Dashboard, Records, Add Entry) and a top header displaying the current developer persona.
*   **Interactive Visualizations:** Integrated **Chart.js** to provide real-time data insights:
    *   Pie Chart showing the distribution of expenses by category.
    *   Bar Chart comparing Income vs Expenses at a glance.
*   **Advanced Data Management:**
    *   **Server-Side Pagination:** Efficiently handles large datasets by fetching records in chunks.
    *   **Filtering & Search:** Real-time search by description and multi-criteria filtering (Type and Category) with debounce logic.
*   **Enhanced UX:**
    *   **Toast System:** Modern feedback notifications for success/error events instead of default alerts.
    *   **Loading States:** Added visual spinners while fetching data for smoother transitions.
    *   **Conditional UI:** Frontend buttons (Delete/Add) are hidden/disabled based on the user's role (Viewer/Analyst/Admin), complementing backend security.
*   **Data Seeding:** On first run, the system now spawns 25+ randomized transactions across realistic categories (Salary, Food, Rent, etc.) to showcase full dashboard capabilities immediately.

## Developer Personas
1.  **Admin Demo:** Full system access (Create, Read, Delete, Dashboard).
2.  **Analyst Demo:** Strategic access (Read records and view Dashboard analytics).
3.  **Viewer Demo:** Restricted access (Read-only view of transaction history).

## Prerequisites & Setup
1.  Install Python 3.11+.
2.  Install dependencies:
    ```bash
    pip install Flask Flask-SQLAlchemy
    ```
3.  Launch the application:
    ```bash
    python app.py
    ```
4.  Navigate to `http://127.0.0.1:5000`.

## Design Philosophy
The UI follows a "Student Portfolio" aesthetic—clean colors (Indigo/Blue), Flexbox/Grid for responsiveness, and a focus on clarity. It avoids heavy frontend frameworks to keep the project lightweight and easily evaluatable by senior engineers interested in core backend and vanilla JS proficiency.

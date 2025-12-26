# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##   - agent: "main_agent"
##     message: "Context or instructions for testing agent"

#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  Aplicación web para gestionar leads de redes sociales (Facebook, Instagram, TikTok) y de entrada manual.
  Incluye: seguimiento de leads, gestión de usuarios con 4 roles, base de datos de leads, historial de conversación,
  integración N8N/WhatsApp, asignación automática de leads por carrera, dashboard, Google Calendar.

backend:
  - task: "API de usuarios con assigned_careers"
    implemented: true
    working: "NA"
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Backend ya tiene soporte para assigned_careers en UserCreate, UserUpdate y UserResponse"

  - task: "Asignación automática de leads por carrera"
    implemented: true
    working: "NA"
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Función find_agent_for_career implementada, se usa al crear leads"

frontend:
  - task: "Selector de carreras en modal Crear Usuario"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/pages/UsersPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Añadido selector múltiple de carreras cuando el rol es 'agente'"

  - task: "Selector de carreras en modal Editar Usuario"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/pages/UsersPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Añadido selector múltiple de carreras cuando el rol es 'agente'"

  - task: "Mostrar carreras asignadas en tabla de usuarios"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/pages/UsersPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Ya implementado anteriormente, columna 'Carreras Asignadas'"

  - task: "Botón copiar teléfono en LeadsPage"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/pages/LeadsPage.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Cambiado de WhatsApp a Copiar Teléfono al portapapeles"

  - task: "Botón copiar teléfono en LeadDetailPage"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/pages/LeadDetailPage.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Cambiado de WhatsApp a Copiar Teléfono al portapapeles"

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 1
  run_ui: true

test_plan:
  current_focus:
    - "Selector de carreras en modal Crear Usuario"
    - "Selector de carreras en modal Editar Usuario"
    - "Asignación automática de leads por carrera"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main_agent"
    message: |
      Se han implementado las siguientes funcionalidades:
      1. Selector múltiple de carreras en los modales de Crear y Editar Usuario (solo visible para rol 'agente')
      2. Botón de copiar teléfono en lugar de WhatsApp (para evitar bloqueos)
      
      Para probar:
      1. Registrar un usuario admin primero para acceder a UsersPage
      2. Crear un agente con carreras asignadas (ej: Ingeniería, Medicina)
      3. Verificar que las carreras se muestran en la tabla
      4. Editar el agente y verificar que las carreras se pueden modificar
      5. Crear un lead con carrera de interés que coincida con un agente
      6. Verificar que el lead se asigna automáticamente al agente correcto
      7. Probar el botón de copiar teléfono en la lista de leads

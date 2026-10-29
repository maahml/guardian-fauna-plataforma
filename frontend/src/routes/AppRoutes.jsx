import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import AppLayout from '../components/layout/AppLayout';
import { ROLES } from '../utils/constants';

import Login from '../pages/auth/Login';
import RequestAccess from '../pages/auth/RequestAccess';
import Dashboard from '../pages/dashboard/Dashboard';
import OperationsList from '../pages/operations/OperationsList';
import OperationCreate from '../pages/operations/OperationCreate';
import OccurrencesList from '../pages/occurrences/OccurrencesList';
import OccurrenceCreate from '../pages/occurrences/OccurrenceCreate';
import OccurrenceDetails from '../pages/occurrences/OccurrenceDetails';
import SheltersList from '../pages/shelters/SheltersList';
import ShelterCreate from '../pages/shelters/ShelterCreate';
import Messaging from '../pages/messaging/Messaging';
import AccessRequests from '../pages/auth/AccessRequests';

export default function AppRoutes() {
  return (
    <Routes>
      {/* Páginas disponíveis sem autenticação */}
      <Route path="/login" element={<Login />} />
      <Route path="/solicitar-acesso" element={<RequestAccess />} />

      {/* Páginas internas com o menu do sistema */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/ocorrencias" element={<OccurrencesList />} />
          <Route path="/ocorrencias/:id" element={<OccurrenceDetails />} />
          <Route path="/abrigos" element={<SheltersList />} />

          <Route element={<ProtectedRoute allowedRoles={[ROLES.ADMIN]} />}>
            <Route path="/admin/solicitacoes" element={<AccessRequests />} />
          </Route>

          {/* Acesso para agentes, coordenadores e administradores */}
          <Route element={<ProtectedRoute allowedRoles={[ROLES.AGENTE, ROLES.COORDENADOR, ROLES.ADMIN]} />}>
            <Route path="/ocorrencias/nova" element={<OccurrenceCreate />} />
            <Route path="/mensageria" element={<Messaging />} />
          </Route>

          {/* Acesso restrito a coordenadores e administradores */}
          <Route element={<ProtectedRoute allowedRoles={[ROLES.COORDENADOR, ROLES.ADMIN]} />}>
            <Route path="/operacoes" element={<OperationsList />} />
            <Route path="/operacoes/nova" element={<OperationCreate />} />
            <Route path="/abrigos/novo" element={<ShelterCreate />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

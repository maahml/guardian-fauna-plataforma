import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Home, MapPin, User, KeyRound } from 'lucide-react';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import styles from '../../styles/pages/shelters/Shelters.module.css';
import { sheltersService } from '../../services/sheltersService';

export default function ShelterCreate() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [form, setForm] = useState({
    nomePublico: '',
    especies: '',
    enderecoSigiloso: '',
    responsavelTecnico: '',
    segredoOperacional: '',
  });

  const handleChange = (e) => setForm((p) => ({ ...p, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage('');
    try {
      await sheltersService.create(form);
      navigate('/abrigos');
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Não foi possível salvar o abrigo.');
    } finally { setLoading(false); }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card} style={{ maxWidth: '640px' }}>
        <h1 className={styles.title}>Cadastrar Abrigo / CETAS</h1>
        <p className={styles.subtitle}>
          O endereço e o responsável técnico serão armazenados de forma cifrada.
        </p>

        {errorMessage && <p role="alert" style={{ color: '#fca5a5' }}>{errorMessage}</p>}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Input
            label="Nome Público do Ponto"
            name="nomePublico"
            placeholder="Ex: CETAS Regional Serrana"
            icon={Home}
            value={form.nomePublico}
            onChange={handleChange}
            required
          />
          <Input
            label="Espécies Habilitadas"
            name="especies"
            placeholder="Ex: Passeriformes, Répteis, Felinos"
            value={form.especies}
            onChange={handleChange}
            required
          />
          <Input
            label="Endereço Exato (Sigiloso)"
            name="enderecoSigiloso"
            placeholder="Endereço completo da unidade"
            icon={MapPin}
            value={form.enderecoSigiloso}
            onChange={handleChange}
            required
          />
          <Input
            label="Responsável Técnico"
            name="responsavelTecnico"
            placeholder="Veterinário ou biólogo responsável"
            icon={User}
            value={form.responsavelTecnico}
            onChange={handleChange}
            required
          />
          <Input
            label="Chave da Operação para Cifra"
            name="segredoOperacional"
            type="password"
            placeholder="Chave para proteger os dados deste abrigo"
            icon={KeyRound}
            value={form.segredoOperacional}
            onChange={handleChange}
            minLength={10}
            autoComplete="new-password"
            required
          />
          <div style={{ marginTop: '8px' }}>
            <Button type="submit" loading={loading}>
              Salvar abrigo
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

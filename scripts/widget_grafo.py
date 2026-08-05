class Bridge:
    ...  # Existing Bridge class methods

    def guardar_orbGrafo(self, valor: float) -> None:
        """Salva orbGrado no localStorage e escreve em arquivo para validação""
        try:
            # Salvar no localStorage (fronet)
            if self._win and self._win.evaluate_js:
                self._win.evaluate_js(f"\n                localStorage.setItem('orbGrafo', '{valor}');\n            "")

            # Salvar em arquivo (backend)
            with open(BASE / 'docs' / 'grafo_widget_orbGrafo.json', 'w', encoding='utf-8') as f:
                f.write(f"{valor:.2f}")
        except Exception as e:
            self.debug_log(f'[widget] Error saving orbGrado: {e}')

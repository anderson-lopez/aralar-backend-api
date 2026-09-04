from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_name: str = "facebook/nllb-200-distilled-600M"
    source_lang: str = "spa_Latn"
    target_langs: str = (
        "spa_Latn:Español,eng_Latn:Inglés,fra_Latn:Francés,deu_Latn:Alemán,"
        "ita_Latn:Italiano,por_Latn:Portugués,rus_Cyrl:Ruso,jpn_Jpan:Japonés,"
        "kor_Hang:Coreano,zho_Hans:Chino,arb_Arab:Árabe,eus_Latn:Euskera,"
        "cat_Latn:Catalán,glg_Latn:Gallego,nld_Latn:Neerlandés,swe_Latn:Sueco,"
        "dan_Latn:Danés,nob_Latn:Noruego,fin_Latn:Finlandés,pol_Latn:Polaco,"
        "ces_Latn:Checo,slk_Latn:Eslovaco,hun_Latn:Húngaro,ron_Latn:Rumano,"
        "ukr_Cyrl:Ucraniano,tur_Latn:Turco,hin_Deva:Hindi,vie_Latn:Vietnamita,"
        "ind_Latn:Indonesio,swh_Latn:Suajili"
    )
    host: str = "0.0.0.0"
    port: int = 8000
    device: str = "cpu"
    hf_home: str = "/cache/huggingface"

    @property
    def target_langs_dict(self) -> dict[str, dict[str, str]]:
        result = {}
        for item in self.target_langs.split(","):
            code, name = item.split(":", 1)
            result[code] = {"name": name}
        return result

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

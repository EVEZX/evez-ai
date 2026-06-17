declare class EvezAI {
  constructor(apiKey: string);
  chat: {
    completions: {
      create(params: {
        model: string;
        messages: Array<{role: string; content: string}>;
        max_tokens?: number;
        temperature?: number;
        stream?: boolean;
      }): Promise<any>;
    };
  };
  static MODELS: {
    SMART: "evez-smart";
    CODE: "evez-code";
    FAST: "evez-fast";
    VISION: "evez-vision";
  };
}
export default EvezAI;

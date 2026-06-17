export default function handler(req, res) {
  const MODELS = ['evez-smart','evez-code','evez-fast','evez-vision'];
  res.setHeader('Access-Control-Allow-Origin', '*');
  return res.status(200).json({
    object: 'list',
    data: MODELS.map(id => ({ id, object: 'model', owned_by: 'evez' }))
  });
}
